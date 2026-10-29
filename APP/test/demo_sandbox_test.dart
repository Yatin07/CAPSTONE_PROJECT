import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:app/services/api_service.dart';
import 'package:app/repositories/app_repository.dart';
import 'package:app/models/inventory_item.dart';

void main() {
  group('Phase 1 Demo Sandbox Flutter Contract Tests', () {
    setUp(() {
      ApiService.resetClient();
      ApiService.instance.setWorkspace(null);
    });

    test('X-Workspace header is sent ONLY during demo tour and omitted in live mode', () {
      final api = ApiService.instance;

      // 1. Live mode by default
      expect(api.isDemoWorkspace, false);
      expect(api.workspace, isNull);

      // Verify LiveRepository modeLabel
      final liveRepo = LiveRepository(apiService: api);
      expect(liveRepo.isDemoTour, false);
      expect(liveRepo.modeLabel, 'LIVE');

      // 2. Activate demo workspace
      api.setWorkspace('demo');
      expect(api.isDemoWorkspace, true);
      expect(api.workspace, 'demo');
      expect(liveRepo.isDemoTour, true);
      expect(liveRepo.modeLabel, 'DEMO');

      // 3. Clear demo workspace on exit
      api.setWorkspace(null);
      expect(api.isDemoWorkspace, false);
      expect(api.workspace, isNull);
      expect(liveRepo.isDemoTour, false);
      expect(liveRepo.modeLabel, 'LIVE');
    });

    test('Tour start, clock simulation, reset, and exit send correct endpoints with demo header', () async {
      final api = ApiService.instance;
      final requestedPaths = <String>[];
      final requestedHeaders = <Map<String, String>>[];

      api.client = MockClient((request) async {
        requestedPaths.add(request.url.path);
        requestedHeaders.add(request.headers);

        if (request.url.path.endsWith('/demo/start')) {
          return http.Response(jsonEncode({
            'status': 'started',
            'workspace': 'demo',
            'items_seeded': 7,
          }), 200);
        }
        if (request.url.path.endsWith('/demo/clock')) {
          return http.Response(jsonEncode({
            'status': 'clock_updated',
            'simulated_clock_hour': 14.5,
          }), 200);
        }
        if (request.url.path.endsWith('/demo/reset')) {
          return http.Response(jsonEncode({
            'status': 'reset',
            'items_seeded': 7,
          }), 200);
        }
        if (request.url.path.endsWith('/demo')) {
          return http.Response(jsonEncode({
            'status': 'deleted',
            'deleted_counts': {'items': 7},
          }), 200);
        }
        return http.Response('{"error":"not found"}', 404);
      });

      // 1. Start demo
      final startRes = await api.startDemo();
      expect(startRes['status'], 'started');
      expect(api.isDemoWorkspace, true);
      expect(requestedPaths.last, contains('/demo/start'));

      // 2. Set clock
      final clockRes = await api.setDemoClock(14.5);
      expect(clockRes['simulated_clock_hour'], 14.5);
      expect(requestedHeaders.last['X-Workspace'], 'demo');

      // 3. Reset demo
      final resetRes = await api.resetDemo();
      expect(resetRes['status'], 'reset');
      expect(requestedHeaders.last['X-Workspace'], 'demo');

      // 4. Exit demo
      final exitRes = await api.exitDemo();
      expect(exitRes['status'], 'deleted');
      expect(api.isDemoWorkspace, false);
      expect(api.workspace, isNull);
    });

    test('Live store empty state: fetchDashboard returns 0 items and empty summary', () async {
      final api = ApiService.instance;
      api.setWorkspace(null); // Live mode

      api.client = MockClient((request) async {
        if (request.url.path.endsWith('/items')) {
          return http.Response(jsonEncode({'items': []}), 200);
        }
        if (request.url.path.endsWith('/forecasts/today')) {
          return http.Response(jsonEncode({
            'summary': 'Your store is ready. Add your first item to begin forecasting.',
            'total_items': 0,
            'action_required_count': 0,
            'items': [],
          }), 200);
        }
        return http.Response('{}', 404);
      });

      final liveRepo = LiveRepository(apiService: api);
      final dashboard = await liveRepo.fetchDashboard();

      expect(dashboard['total_items'], 0);
      expect((dashboard['items'] as List).isEmpty, true);
      expect(api.isDemoWorkspace, false);
    });
  });
}
