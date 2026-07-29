# Machine Learning Learning Notes

Welcome to the Machine Learning (ML) learning notes! This file will be updated continuously as we progress through our ML tasks in this project. 

Our goal here is not just to build, but to learn. For every successful task completed within this ML directory, we will document what we did, the technologies we used, and explain the underlying concepts as if teaching them to someone new to the field.

---

## Task 1: Environment Setup & Local vs. Cloud (Colab)

**What we discussed:** We explored the purpose of creating local Python virtual environments versus using a cloud-based service like Google Colab for Machine Learning.

### Teaching Corner: Understanding the Setup Commands

When you see commands like these:
```bash
python -m venv venv
source venv/bin/activate      # or venv\Scripts\activate on Windows
pip install prophet pandas scikit-learn matplotlib jupyter kaggle
```

Here is exactly what they do and why they are necessary for **local development**:

1. **Environment Initialization:** `python -m venv venv`
   - **What it is:** The `venv` module provides support for creating lightweight "virtual environments" with their own independent site directories, isolated from system directories.
   - **Why it is used:** Python dependency resolution occurs globally by default. If multiple projects require divergent, incompatible versions of the same dependency, installing them globally leads to version conflicts. A virtual environment isolates the `sys.path` and standard library copies, ensuring project-specific dependencies are maintained within a discrete, localized filesystem hierarchy.
   - **Syntax Breakdown:** 
     - `python`: Invokes the standard Python interpreter.
     - `-m venv`: Executes the `venv` module as a script.
     - `venv`: The designated target directory path where the environment binaries and libraries will be generated.

2. **Environment Activation:** `source venv/bin/activate` (POSIX) or `venv\Scripts\activate` (Windows)
   - **What it is:** A shell script that modifies the current session's environment variables.
   - **Why it is used:** To utilize the isolated binaries, the operating system's `$PATH` variable must prioritize the virtual environment's `bin` (or `Scripts`) directory over the system-wide executable paths. Activation seamlessly achieves this modification for the duration of the terminal session.
   - **Syntax Breakdown (Windows):** `venv\Scripts\activate` executes the `activate.bat` or `activate.ps1` script located within the environment's directory.

3. **Dependency Resolution & Installation:** `pip install prophet pandas scikit-learn matplotlib jupyter kaggle`
   - **What it is:** `pip` (Pip Installs Packages) is the package installer for Python, querying the Python Package Index (PyPI).
   - **Why it is used:** To fetch and compile the external libraries required for execution:
     - `prophet`: Core forecasting library utilizing an additive model.
     - `pandas`: Data structure provisioning for DataFrame-based operations.
     - `scikit-learn`: Implementation of standard predictive data analysis algorithms.
     - `matplotlib`: Foundation for static, animated, and interactive visualizations.
     - `jupyter`: Web-based interactive computing architecture.
     - `kaggle`: Official CLI interface for Kaggle API dataset procurement.
   - **Syntax Breakdown:** `pip install <package1> <package2> ...` instructs the package manager to sequentially download and resolve the dependency trees for each declared package space-separated string.

### Alternative Architectural Approach: Cloud-Hosted Execution (Google Colab)

Opting for Google Colaboratory circumvents local provisioning requirements through a managed cloud infrastructure.

- **Infrastructure Abstraction:** Google Colab provisions a containerized Jupyter Notebook environment backed by ephemeral, virtualized hardware (including GPUs). Consequently, local shell initialization (`python -m venv` and `activate`) is structurally unnecessary, as isolation is handled at the container level.
- **Pre-configured Runtime:** Fundamental data science dependencies (e.g., `pandas`, `scikit-learn`, `matplotlib`) are pre-compiled and injected into the runtime environment by default.
- **Syntax Adaptations:** When non-standard packages (`prophet`, `kaggle`) are required, they must be provisioned during runtime via notebook cells leveraging the shell escape character `!`.
  - *Syntax:* `!pip install prophet` executes the bash command within the underlying container rather than interpreting it as Python logic.
- **Trade-offs:** 
  - *Advantages:* Zero configuration latency, hardware offloading, and deterministic execution environments.
  - *Disadvantages:* State volatility (the filesystem resets upon kernel death or session timeout) necessitating redundant dataset acquisition and dependency installation upon each initialization.

---

## Task 2: Exploratory Data Analysis (EDA) of Time Series Datasets

**What we did:** We programmatically analyzed four raw datasets (Rossmann, French Bakery, Grocery Inventory, and SKU Sales) stored in disparate file formats (`.csv` and `.parquet`) to evaluate their structural viability for univariate time series forecasting using Facebook's Prophet model. The evaluation criteria mandated a daily chronological granularity and a minimum historical depth of 1.5 years (547 days).

### Technical Breakdown: Dataset Ingestion and Introspection

1. **Format-Agnostic Data Ingestion:**
   - **What it is:** The utilization of pandas' high-performance parsing libraries (`read_csv` and `read_parquet`) to deserialize disk-bound data into in-memory `DataFrame` objects.
   - **Why it is used in an engineering context:** Flat files (`.csv`) offer maximum interoperability but suffer from inefficient storage and lack of strict schemas. Columnar storage formats like Parquet (`.parquet`) enforce strong typing, utilize efficient compression (e.g., Snappy), and optimize I/O via predicate pushdown and column pruning, making them significantly more performant for large-scale analytical workloads.
   - **Syntax Breakdown:**
     - `pd.read_csv(file_path, low_memory=False)`: Invokes the C-engine parser for comma-separated values. The `low_memory=False` directive forces the parser to process the entire file to accurately infer `dtypes` instead of chunking, preventing silent upcasting errors at the cost of higher RAM consumption.
     - `pd.read_parquet(file_path)`: Delegates deserialization to the `pyarrow` backend, which memory-maps the Parquet file and translates its columnar schema directly into pandas' internal block manager representation.

2. **Temporal Type Inference and Coercion:**
   - **What it is:** The algorithmic detection and conversion of string-encoded temporal data (`object` dtype) into standard `datetime64[ns]` representations.
   - **Why it is used:** Raw datasets frequently encode timestamps as ISO 8601 strings or variant formats. To compute temporal differentials (e.g., calculating the time series duration) and aggregate by time periods, these vectors must be cast to a numeric, machine-readable chronological type.
   - **Syntax Breakdown:**
     - `pd.to_datetime(df[col], errors='coerce')`: The vectorized datetime parser. `errors='coerce'` acts as a fail-safe instruction during the parsing routine; when the parser encounters a non-conformant or corrupted string that violates the inferred datetime format, it overrides the default `ValueError` exception and instead injects a `NaT` (Not a Time) sentinel value, preserving the operational integrity of the pipeline.

3. **Granularity and Frequency Analysis:**
   - **What it is:** Determining the structural cadence of the dataset by evaluating chronological deltas between unique timestamps.
   - **Why it is used:** Time series forecasting models expect sequential observations sampled at equidistant temporal intervals. Assessing the `median_diff` of the sorted unique dates validates the sampling frequency (e.g., daily `freq='D'`). Furthermore, calculating the `mean_rows_per_date` exposes whether the data is already aggregated to a univariate series or if it remains at a transaction/entity level (requiring a subsequent `groupby` aggregation before modeling).
   - **Syntax Breakdown:**
     - `df[col].dt.date.value_counts()`: Extrapolates the date component and computes the cardinality of each unique day.
     - `pd.Series(unique_dates).diff().dt.days.dropna().median()`: A chained analytical operation that calculates the first discrete difference along the temporal vector, extracts the scalar integer representation (days), removes resulting `NaN` values (from the first index), and computes the 50th percentile (median) to robustly determine the dominant interval cadence, impervious to isolated anomalies.

---

## Task 3: Dataset Evaluation Execution Results & Verdicts

**What we did:** We executed the dataset evaluation script (`analyze_datasets.py`) against the actual raw datasets to definitively classify their usability for Prophet modeling. The execution involved initializing the Python interpreter to dynamically traverse the `data/raw` directory and apply our evaluation heuristics.

### Technical Breakdown: Execution and Result Synthesis

1. **Script Execution:**
   - **What it is:** Invoking the Python runtime to execute the `analyze_datasets.py` script.
   - **Why it is used in an engineering context:** To transition from theoretical script design to empirical validation, ensuring that the logic defined for parsing, typing, and granularity checks correctly handles the actual anomalies and structure of the downloaded data.
   - **Syntax Breakdown:**
     - `python analyze_datasets.py`: Instructs the CPython interpreter to parse and execute the source code sequentially, instantiating the runtime environment and executing the byte-compiled operations against the raw dataset artifacts.

2. **Empirical Findings (Verdicts):**
   - **Bakery sales.csv:** Granularity is daily, span from 2021-01-02 to 2022-09-30. **Verdict: USABLE FOR PROPHET TRAINING**
   - **Grocery_Inventory_and_Sales_Dataset.csv:** Only 365 days of history. **Verdict: NOT USABLE FOR TRAINING — too short (history is 365 days, need >= 547)**
   - **Store_Sales_Price_Elasticity_Promotions_Data.parquet:** Daily granularity, span from 2021-11-01 to 2024-03-31. **Verdict: USABLE FOR PROPHET TRAINING**
   - **train.csv:** Daily granularity, 2013-01-01 to 2015-07-31. **Verdict: USABLE FOR PROPHET TRAINING**
   - **test.csv:** History is 47 days. **Verdict: NOT USABLE FOR TRAINING — too short**
   - **store.csv & sample_submission.csv:** No date columns identified. **Verdict: NOT USABLE FOR TRAINING — missing real dates**

---

## Task 4: Prophet-Ready Data Pipeline Construction

**What we did:** We engineered a data processing pipeline (`process_datasets.py`) to transform the raw, disparate datasets into a standardized, Prophet-ready schema within the `data/processed/` directory.

### Technical Breakdown: Data Transformations and Standardization

1. **Temporal Aggregation and Standardization:**
   - **What it is:** Transforming transaction-level records into discrete, daily univariate series for each entity.
   - **Why it is used:** Prophet requires exactly two core columns per series: `ds` (a temporal index) and `y` (the numeric target). Over-granular data (e.g., intra-day timestamps or multiple SKUs without explicit entity grouping) violates the algorithm's assumption of a single observation per time step.
   - **Syntax Breakdown:**
     - `df.groupby(['ds', 'Store_Number']).agg({'y': 'sum'})`: Aggregates overlapping dates per entity via summation, ensuring a rigid 1:1 mapping between a date-entity pair and its target value.

2. **Temporal Gap Imputation (Reindexing):**
   - **What it is:** Detecting missing intervals within the time series and filling them using forward-fill (`ffill`).
   - **Why it is used:** While Prophet is relatively resilient to missing data, extensive gaps disrupt the calculation of seasonal Fourier terms and autoregressive components. We quantified 37 missing date gaps in the Bakery dataset and explicitly imputed them to maintain continuous signal integrity.
   - **Syntax Breakdown:**
     - `pd.date_range(start, end, freq='D')`: Generates a complete chronological vector mapping every calendar day between the bounds.
     - `df.reindex(date_range)`: Expands the DataFrame's index to match the complete vector, injecting `NaN` values at previously non-existent indices.
     - `df['y'].ffill()`: Propagates the last valid observation forward to synthesize continuity, avoiding the stark, artificial drops caused by zero-filling.

3. **Feature Joins and Conditional Filtering:**
   - **What it is:** Augmenting the primary sales series (Rossmann `train.csv`) with static store attributes (`store.csv`) and eliminating zero-sales days caused by structural closures.
   - **Why it is used:** If a store is physically closed (`Open == 0`), the resulting zero sales do not represent low consumer demand; they represent a structural constraint. Feeding these zeros into Prophet would severely downward-bias the trend and daily seasonality.
   - **Syntax Breakdown:**
     - `df_train.merge(df_store, on='Store', how='left')`: A standard left outer join resolving referential integrity between fact and dimension tables.
     - `df[df['Open'] != 0]`: A boolean mask to drop structurally constrained non-demand days prior to modeling.
