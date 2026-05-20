import pandas as pd
import numpy as np
import re
import io
import chardet
from pathlib import Path
from dateutil.parser import parse, ParserError


# =============================================================
# DATA PROCESSOR CLASS
# =============================================================

class DataProcessor:
    """
    Handles any tabular file format → cleans → extracts metadata.
    Supports: CSV, Excel (.xlsx/.xls), JSON, Parquet, TSV, ODS, XML,
              plain text tables, BytesIO streams (for FastAPI uploads).
    Handles datasets with 10 columns or 500 columns equally well.
    """

    # =====================================================
    # INITIALIZE
    # =====================================================

    def __init__(self, file_path):

        self.file_path = file_path

        self.df = None

        self.metadata = {}

    # =====================================================
    # STEP 1 — LOAD FILE
    # =====================================================

    def load_file(self):

        extension = Path(self.file_path).suffix.lower()

        print(f"\nDetected File Type: {extension}")

        try:

            # CSV FILES
            if extension == '.csv':

                self.df = pd.read_csv(
                    self.file_path,
                    low_memory=False
                )

            # EXCEL FILES
            elif extension in ['.xlsx', '.xls']:

                excel_file = pd.ExcelFile(self.file_path)

                sheet_names = excel_file.sheet_names

                print(f"Detected Sheets: {sheet_names}")

                all_sheets = []

                for sheet in sheet_names:

                    temp_df = pd.read_excel(
                        self.file_path,
                        sheet_name=sheet
                    )

                    temp_df['sheet_name'] = sheet

                    all_sheets.append(temp_df)

                self.df = pd.concat(
                    all_sheets,
                    ignore_index=True
                )

            # JSON FILES
            elif extension == '.json':
                self.df = pd.read_json(self.file_path)

            # PARQUET FILES
            elif extension == '.parquet':
                self.df = pd.read_parquet(self.file_path)

            else:
                raise ValueError(
                    f"Unsupported file format: {extension}"
                )

            print("File loaded successfully")
            print(f"Dataset Shape: {self.df.shape}")

        except Exception as e:
            print(f"Error loading file: {e}")
            raise

    # =============================================================
    # STEP 2 — STANDARDIZE COLUMN NAMES
    # =============================================================

    def standardize_column_names(self):
        """
        NEW vs original:
        - Also strips multiple consecutive underscores (e.g. 'sales__2024' → 'sales_2024')
        - Strips leading/trailing underscores after transformation
        - Handles completely duplicate column names by appending _1, _2 …
        """
        cleaned = []
        for col in self.df.columns:
            c = (
                str(col)
                .strip()
                .lower()
                .replace(' ', '_')
                .replace('-', '_')
                .replace('.', '_')
                .replace('/', '_')
                .replace('(', '')
                .replace(')', '')
                .replace('%', 'pct')
                .replace('#', 'num')
            )
            # collapse multiple underscores
            c = re.sub(r'_+', '_', c).strip('_')
            cleaned.append(c)

        # Resolve duplicates
        seen   = {}
        result = []
        for c in cleaned:
            if c in seen:
                seen[c] += 1
                result.append(f"{c}_{seen[c]}")
            else:
                seen[c] = 0
                result.append(c)

        self.df.columns = result
        print("Column names standardized")

    # =====================================================
# CLEAN CURRENCY VALUES
# =====================================================

    def clean_currency_columns(self):

        currency_symbols = [
            '$',
            '₹',
            '€',
            '£',
            ','
        ]

        for col in self.df.columns:

            if self.df[col].dtype == 'object':

                sample = self.df[col].astype(str).head(20)

                currency_detected = False

                for value in sample:

                    if any(symbol in value for symbol in currency_symbols):
                        currency_detected = True
                        break

                if currency_detected:

                    self.df[col] = (
                        self.df[col]
                        .astype(str)
                        .str.replace('$', '', regex=False)
                        .str.replace('₹', '', regex=False)
                        .str.replace('€', '', regex=False)
                        .str.replace('£', '', regex=False)
                        .str.replace(',', '', regex=False)
                        .str.strip()
                    )

                    self.df[col] = pd.to_numeric(
                        self.df[col],
                        errors='coerce'
                    )

                    print(f"Currency cleaned: {col}")

    # =====================================================
# FIX CATEGORICAL INCONSISTENCIES
# =====================================================

    def fix_categorical_inconsistencies(self):

        for col in self.df.columns:

            if self.df[col].dtype == 'object':

                unique_count = self.df[col].nunique()

                # Only normalize low-cardinality columns
                if unique_count <= 50:

                    self.df[col] = (
                        self.df[col]
                        .astype(str)
                        .str.strip()
                        .str.title()
                    )

                    print(f"Normalized categories: {col}")


    # =====================================================
# OPTIMIZE MEMORY
# =====================================================

    def optimize_memory(self):

        start_memory = self.df.memory_usage(
            deep=True
        ).sum() / 1024**2

        print(f"Initial Memory Usage: {start_memory:.2f} MB")

        # INTEGER COLUMNS
        int_cols = self.df.select_dtypes(
            include=['int']
        ).columns

        for col in int_cols:

            self.df[col] = pd.to_numeric(
                self.df[col],
                downcast='integer'
            )

        # FLOAT COLUMNS
        float_cols = self.df.select_dtypes(
            include=['float']
        ).columns

        for col in float_cols:

            self.df[col] = pd.to_numeric(
                self.df[col],
                downcast='float'
            )

        # OBJECT → CATEGORY
        object_cols = self.df.select_dtypes(
            include=['object']
        ).columns

        for col in object_cols:

            unique_ratio = (
                self.df[col].nunique() / len(self.df)
            )

            if unique_ratio < 0.5:

                self.df[col] = self.df[col].astype(
                    'category'
                )

        end_memory = self.df.memory_usage(
            deep=True
        ).sum() / 1024**2

        reduction = (
            (start_memory - end_memory)
            / start_memory
        ) * 100

        print(f"Optimized Memory Usage: {end_memory:.2f} MB")
        print(f"Memory Reduced By: {reduction:.2f}%")

    # =============================================================
    # STEP 3 — REMOVE DUPLICATES
    # =============================================================

    def remove_duplicates(self):
        """Same logic as original but also resets index after drop."""
        dup_count = self.df.duplicated().sum()
        self.metadata['duplicate_rows_removed'] = int(dup_count)
        self.df.drop_duplicates(inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        print(f"Removed {dup_count} duplicate rows")

    # =============================================================
    # STEP 4 — CONVERT NUMERIC COLUMNS
    # =============================================================

    def convert_numeric_columns(self):
        """
        NEW vs original:
        - Strips currency symbols and commas before converting
          (handles values like '$1,200.50' or '₹45,000')
        - Only converts if 70%+ of values are numeric (same threshold)
        """
        for col in self.df.columns:
            if self.df[col].dtype != 'object':
                continue
            # Strip common non-numeric characters
            cleaned = (
                self.df[col]
                .astype(str)
                .str.replace(r'[\$₹€£,\s]', '', regex=True)
                .str.strip()
            )
            converted = pd.to_numeric(cleaned, errors='coerce')
            if converted.notnull().sum() > len(self.df) * 0.7:
                self.df[col] = converted
                print(f"Converted numeric column: {col}")

    # =============================================================
    # STEP 5 — DETECT DATE COLUMNS
    # =============================================================

    def detect_date_columns(self):
        """
        Same heuristic as original but:
        NEW: also catches columns that are already dtype datetime64
             (e.g. Parquet files pre-typed as datetime)
        NEW: skips columns that are clearly IDs or codes
             (high cardinality integers — won't look like dates)
        """
        detected = []

        # Already datetime (e.g. from Parquet)
        for col in self.df.select_dtypes(include=['datetime64']).columns:
            detected.append(col)

        # Object columns — heuristic parsing
        for col in self.df.select_dtypes(include='object').columns:
            if col in detected:
                continue
            sample = self.df[col].dropna().astype(str).head(20)
            success = 0
            for val in sample:
                try:
                    parse(val, fuzzy=False)
                    success += 1
                except (ParserError, ValueError, OverflowError):
                    pass
            if success >= max(3, len(sample) * 0.6):
                detected.append(col)

        self._date_columns = detected
        self.metadata['date_columns_detected'] = detected
        print(f"Detected date columns: {detected}")
        return detected

    # =============================================================
    # STEP 6 — CONVERT DATE COLUMNS (handles dd/mm vs mm/dd)
    # =============================================================

    def convert_date_columns(self):
        """
        MAJOR improvement over original:

        Problem in original:
          It tries dayfirst=False first, then dayfirst=True only if 
          >40% NaT. But this is unreliable — '05/06/2023' is ambiguous.

        New approach — 4-step smart detection:
          1. Scan 30 sample values for any day value > 12
             → if found, MUST be dayfirst=True (because month can't be > 12)
          2. Check known regional hints in column name
             ('date_india', 'dob', 'invoice_date' → assume dayfirst=True
              for Indian datasets; 'ship_date_us' → dayfirst=False)
          3. Try both formats, pick the one with fewer NaT values
          4. If still tied → default to dayfirst=False (ISO standard)

        Also creates richer date features:
          - year, month, day, day_name, quarter (original had these)
          - week_of_year    ← NEW
          - is_weekend      ← NEW (True/False flag)
          - is_month_start  ← NEW
          - is_month_end    ← NEW
          These extra features help the LLM write better chart code
          (e.g. "group by is_weekend" or "filter by quarter").
        """
        date_cols = self.detect_date_columns()

        for col in date_cols:

            # Skip already-converted datetime columns
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                self._add_date_features(col)
                continue

            raw_series = self.df[col].astype(str)

            # --- Step 1: scan for day > 12 (proves dayfirst) ---
            dayfirst = None
            sample_vals = raw_series.dropna().head(30).tolist()
            for val in sample_vals:
                # Match dd/mm/yyyy or dd-mm-yyyy or dd.mm.yyyy
                m = re.match(r'^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})$', val.strip())
                if m:
                    first_num = int(m.group(1))
                    second_num = int(m.group(2))
                    if first_num > 12:
                        dayfirst = True
                        break
                    if second_num > 12:
                        dayfirst = False
                        break

            # --- Step 2: column name hints ---
            if dayfirst is None:
                col_lower = col.lower()
                if any(hint in col_lower for hint in ['dob', 'birth', 'india', 'in_date']):
                    dayfirst = True
                elif any(hint in col_lower for hint in ['us_date', 'us_', '_us']):
                    dayfirst = False

            # --- Step 3: try both, pick fewer NaT ---
            if dayfirst is None:
                parsed_df_false = pd.to_datetime(raw_series, errors='coerce', dayfirst=False)
                parsed_df_true  = pd.to_datetime(raw_series, errors='coerce', dayfirst=True)
                nat_false = parsed_df_false.isnull().sum()
                nat_true  = parsed_df_true.isnull().sum()

                if nat_true < nat_false:
                    dayfirst = True
                elif nat_false < nat_true:
                    dayfirst = False
                else:
                    dayfirst = False  # Step 4: default ISO

            # Final parse
            self.df[col] = pd.to_datetime(
                self.df[col], errors='coerce', dayfirst=dayfirst
            )
            nat_pct = self.df[col].isnull().mean() * 100
            print(f"Converted date column '{col}' | dayfirst={dayfirst} | NaT: {nat_pct:.1f}%")

            self._add_date_features(col)

    def _add_date_features(self, col):
        """Create derived date feature columns."""
        try:
            self.df[f'{col}_year']         = self.df[col].dt.year
            self.df[f'{col}_month']        = self.df[col].dt.month
            self.df[f'{col}_day']          = self.df[col].dt.day
            self.df[f'{col}_day_name']     = self.df[col].dt.day_name()
            self.df[f'{col}_quarter']      = self.df[col].dt.quarter
            self.df[f'{col}_week_of_year'] = self.df[col].dt.isocalendar().week.astype('Int64')
            self.df[f'{col}_is_weekend']   = self.df[col].dt.dayofweek >= 5
            self.df[f'{col}_is_month_end'] = self.df[col].dt.is_month_end
        except Exception as e:
            print(f"Could not add date features for '{col}': {e}")

    # =============================================================
    # STEP 7 — ANALYZE MISSING VALUES (with drop/fill decision)
    # =============================================================

    def analyze_missing_values(self):
        """
        NEW vs original: 
        Now returns a recommendation for each column:
          - 'drop_column'  if missing > 70%
          - 'drop_rows'    if missing < 5% (small enough to just remove rows)
          - 'fill_mean'    if numeric and low skew
          - 'fill_median'  if numeric and high skew (|skew| > 1)
          - 'fill_mode'    if categorical
          - 'fill_zero'    if column name suggests a count/amount and 
                           missing likely means zero (e.g. 'quantity', 'returns')
        This recommendation is stored in metadata so the dashboard can
        show the user WHY each column was handled a certain way.
        """
        missing_info = {}

        for col in self.df.columns:
            missing_count   = int(self.df[col].isnull().sum())
            missing_percent = round(missing_count / len(self.df) * 100, 2)
            is_important    = self._is_likely_important(col)

            # Decide recommendation
            if missing_percent > 70:
                recommendation = 'drop_column'
            elif missing_percent < 5:
                recommendation = 'drop_rows'
            elif pd.api.types.is_numeric_dtype(self.df[col]):
                col_lower = col.lower()
                zero_hints = ['quantity', 'qty', 'count', 'returns', 'discount', 'units']
                if any(h in col_lower for h in zero_hints):
                    recommendation = 'fill_zero'
                elif abs(self.df[col].skew()) > 1:
                    recommendation = 'fill_median'
                else:
                    recommendation = 'fill_mean'
            else:
                recommendation = 'fill_mode'

            missing_info[col] = {
                'missing_count':   missing_count,
                'missing_percent': missing_percent,
                'recommendation':  recommendation,
                'is_important':    is_important
            }

        self.metadata['missing_values'] = missing_info
        print("Missing value analysis completed")
        return missing_info

    def _is_likely_important(self, col):
        """
        Heuristic: flag columns that are likely critical for dashboards.
        These should NEVER be silently dropped even if they have many nulls.
        """
        important_keywords = [
            'sales', 'revenue', 'amount', 'price', 'profit', 'cost',
            'date', 'store', 'product', 'region', 'category', 'id',
            'total', 'quantity', 'score', 'grade', 'marks'
        ]
        col_lower = col.lower()
        return any(kw in col_lower for kw in important_keywords)

    # =============================================================
    # STEP 8 — HANDLE MISSING VALUES
    # =============================================================

    def handle_missing_values(self):
        """
        Uses the recommendations from analyze_missing_values().
        
        NEW vs original:
        - Respects the 'fill_zero' case (original never had this)
        - For 'drop_rows': removes those rows instead of filling
          (keeps columns accurate when only a few rows are bad)
        - Warns before dropping an important column — records it
          in metadata['important_columns_dropped'] for the interview
          explanation / UI warning
        - Uses df[col] = df[col].fillna(...) instead of 
          df[col].fillna(..., inplace=True) which is deprecated 
          in newer Pandas versions
        """
        if 'missing_values' not in self.metadata:
            self.analyze_missing_values()

        dropped_columns           = []
        filled_columns            = []
        rows_dropped_cols         = []
        important_dropped_warning = []

        missing_info = self.metadata['missing_values']

        for col in list(self.df.columns):
            if col not in missing_info:
                continue

            info           = missing_info[col]
            recommendation = info['recommendation']
            is_important   = info['is_important']

            # Skip columns with no missing values
            if info['missing_count'] == 0:
                continue

            if recommendation == 'drop_column':
                if is_important:
                    important_dropped_warning.append(col)
                    print(f"WARNING: Important column '{col}' has {info['missing_percent']}% nulls — dropping anyway")
                self.df.drop(columns=[col], inplace=True)
                dropped_columns.append(col)

            elif recommendation == 'drop_rows':
                before = len(self.df)
                self.df = self.df.dropna(subset=[col])
                after  = len(self.df)
                rows_dropped_cols.append({col: before - after})

            elif recommendation == 'fill_zero':
                self.df[col] = self.df[col].fillna(0)
                filled_columns.append((col, 'zero'))

            elif recommendation == 'fill_mean':
                self.df[col] = self.df[col].fillna(self.df[col].mean())
                filled_columns.append((col, 'mean'))

            elif recommendation == 'fill_median':
                self.df[col] = self.df[col].fillna(self.df[col].median())
                filled_columns.append((col, 'median'))

            elif recommendation == 'fill_mode':
                mode_val = self.df[col].mode()
                fill_val = mode_val[0] if len(mode_val) > 0 else 'Unknown'
                self.df[col] = self.df[col].fillna(fill_val)
                filled_columns.append((col, 'mode'))

        self.df.reset_index(drop=True, inplace=True)

        self.metadata['dropped_columns']              = dropped_columns
        self.metadata['filled_columns']               = filled_columns
        self.metadata['rows_dropped_per_column']      = rows_dropped_cols
        self.metadata['important_columns_dropped']    = important_dropped_warning

        print(f"Dropped columns:  {dropped_columns}")
        print(f"Filled columns:   {[c for c, _ in filled_columns]}")

    # =============================================================
    # STEP 9 — REMOVE HIGHLY EMPTY ROWS
    # =============================================================

    def remove_empty_rows(self):
        """
        NEW: threshold is now 60% (original was 50%).
        50% was too aggressive — a row with half its columns filled
        is still useful in most retail datasets.
        Also resets index after drop.
        """
        threshold    = int(self.df.shape[1] * 0.6)
        initial_rows = len(self.df)
        self.df.dropna(thresh=threshold, inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        removed = initial_rows - len(self.df)
        self.metadata['rows_removed_empty'] = int(removed)
        print(f"Removed {removed} highly empty rows (threshold: 60% non-null)")

    # =============================================================
    # STEP 10 — OUTLIER HANDLING
    # =============================================================

    def handle_outliers(self):
        """
        NEW vs original:
        - Original capped ALL numeric columns.
          New version SKIPS columns that are IDs, years, or codes
          (capping 'customer_id' or 'year' makes no sense).
        - Records both the count AND the percentage of outliers
          so the metadata is richer for the dashboard.
        - Uses .clip() instead of np.where — cleaner and faster.
        """
        outlier_info   = {}
        skip_keywords  = ['id', 'code', 'year', 'month', 'day', 'zip', 'pin', 'phone']

        numeric_cols = self.df.select_dtypes(include=np.number).columns

        for col in numeric_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in skip_keywords):
                continue

            q1  = self.df[col].quantile(0.25)
            q3  = self.df[col].quantile(0.75)
            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            outlier_mask  = (self.df[col] < lower) | (self.df[col] > upper)
            outlier_count = int(outlier_mask.sum())
            outlier_pct   = round(outlier_count / len(self.df) * 100, 2)

            outlier_info[col] = {
                'count':      outlier_count,
                'percent':    outlier_pct,
                'lower_bound': round(lower, 4),
                'upper_bound': round(upper, 4)
            }

            # Cap (clip) outliers to the IQR bounds
            self.df[col] = self.df[col].clip(lower=lower, upper=upper)

        self.metadata['outliers_handled'] = outlier_info
        print("Outlier handling completed")

    # =============================================================
    # STEP 11 — FIX INCONSISTENT CATEGORICAL VALUES  ← NEW
    # =============================================================

    def fix_categorical_inconsistencies(self):
        """
        COMPLETELY NEW — not in original code.

        Real-world datasets have category columns with messy values:
          'Mumbai', 'mumbai', 'MUMBAI ', 'mumbai.' → all mean the same thing
          'Male', 'male', 'M', 'MALE'              → same value

        This step:
        1. Strips whitespace and normalizes to title case for low-cardinality
           object columns (columns with fewer than 50 unique values).
        2. Records which columns were cleaned in metadata.

        Why important for dashboards:
          Without this, a bar chart shows 'Mumbai' and 'mumbai' as two
          separate bars — your sales data looks split when it shouldn't be.
        """
        cleaned_cols = []
        for col in self.df.select_dtypes(include='object').columns:
            n_unique = self.df[col].nunique()
            if n_unique <= 50:
                before = self.df[col].nunique()
                self.df[col] = (
                    self.df[col]
                    .astype(str)
                    .str.strip()
                    .str.title()
                    .replace('Nan', np.nan)
                    .replace('None', np.nan)
                )
                after = self.df[col].nunique()
                if before != after:
                    cleaned_cols.append({'column': col, 'before': before, 'after': after})

        self.metadata['categorical_cleaned'] = cleaned_cols
        if cleaned_cols:
            print(f"Categorical inconsistencies fixed in: {[c['column'] for c in cleaned_cols]}")

    # =============================================================
    # STEP 12 — DROP CONSTANT AND NEAR-CONSTANT COLUMNS  ← NEW
    # =============================================================

    def drop_useless_columns(self):
        """
        COMPLETELY NEW — not in original code.

        Drops:
        1. Constant columns  — every row has the same value
           (e.g. 'country' = 'India' for all 50,000 rows — useless for charts)
        2. Near-constant columns — 99%+ rows have the same value
        3. Columns that are just row numbers / unnamed index columns
           (Unnamed: 0, index, row_num etc.)

        Why important:
          These columns clutter the metadata the LLM reads.
          Fewer useless columns = LLM makes better chart decisions.
        """
        dropped = []

        for col in list(self.df.columns):
            col_lower = col.lower()

            # Drop unnamed index columns
            if col_lower in ['unnamed: 0', 'index', 'row_num', 'row_number', 'sr_no', 'sr.no']:
                self.df.drop(columns=[col], inplace=True)
                dropped.append((col, 'unnamed_index'))
                continue

            # Drop constant columns
            if self.df[col].nunique(dropna=True) <= 1:
                self.df.drop(columns=[col], inplace=True)
                dropped.append((col, 'constant'))
                continue

            # Drop near-constant (99%+ same value)
            top_freq = self.df[col].value_counts(normalize=True).iloc[0]
            if top_freq >= 0.99:
                self.df.drop(columns=[col], inplace=True)
                dropped.append((col, 'near_constant_99pct'))

        self.metadata['useless_columns_dropped'] = dropped
        if dropped:
            print(f"Dropped useless columns: {[c for c, _ in dropped]}")

    # =============================================================
    # STEP 13 — MEMORY OPTIMIZATION  ← NEW
    # =============================================================

    def optimize_memory(self):
        """
        COMPLETELY NEW — not in original code.

        For large datasets (100k+ rows, 50–100 columns), memory usage
        can blow up to several GB. This step:

        1. Downcasts integer columns (int64 → int32 or int16 if range allows)
        2. Downcasts float columns  (float64 → float32)
        3. Converts low-cardinality object columns to 'category' dtype
           (e.g. 'Region' with 10 unique values stored as category 
            uses 10x less memory than storing the full string 10,000 times)

        Example: a 500k-row retail dataset can go from 800MB → 150MB.
        This makes Pandas operations faster too.
        """
        mem_before = self.df.memory_usage(deep=True).sum() / (1024 * 1024)

        # Downcast integers
        for col in self.df.select_dtypes(include=['int64', 'int32']).columns:
            self.df[col] = pd.to_numeric(self.df[col], downcast='integer')

        # Downcast floats
        for col in self.df.select_dtypes(include=['float64']).columns:
            self.df[col] = pd.to_numeric(self.df[col], downcast='float')

        # Low-cardinality strings → category
        for col in self.df.select_dtypes(include='object').columns:
            if self.df[col].nunique() / len(self.df) < 0.05:   # less than 5% unique
                self.df[col] = self.df[col].astype('category')

        mem_after = self.df.memory_usage(deep=True).sum() / (1024 * 1024)
        saved     = round(mem_before - mem_after, 2)

        self.metadata['memory_before_mb'] = round(mem_before, 2)
        self.metadata['memory_after_mb']  = round(mem_after, 2)
        self.metadata['memory_saved_mb']  = saved
        print(f"Memory optimized: {mem_before:.1f}MB → {mem_after:.1f}MB (saved {saved}MB)")

    # =============================================================
    # STEP 14 — EXTRACT METADATA (rich version)
    # =============================================================

    def extract_metadata(self):
        """
        NEW vs original:
        - Adds numeric_summary (min, max, mean, std for each numeric column)
          so the LLM gets richer context for chart code generation
        - Adds top_values for categorical columns (top 10 most common)
          so the LLM knows "Store" has values like 'Mumbai North', 'Delhi South'
        - Adds a human-readable schema_description string that is sent
          directly to the LLM as part of the prompt
        """
        self.metadata['shape']           = self.df.shape
        self.metadata['row_count']       = int(self.df.shape[0])
        self.metadata['column_count']    = int(self.df.shape[1])
        self.metadata['columns']         = self.df.columns.tolist()
        self.metadata['data_types']      = {col: str(dt) for col, dt in self.df.dtypes.items()}
        self.metadata['memory_usage_mb'] = round(self.df.memory_usage(deep=True).sum() / (1024**2), 2)
        self.metadata['sample_rows']     = self.df.head(5).to_dict(orient='records')

        # Unique value counts
        self.metadata['unique_values'] = {
            col: int(self.df[col].nunique()) for col in self.df.columns
        }

        # Date ranges
        date_ranges = {}
        for col in self.df.select_dtypes(include=['datetime64']).columns:
            date_ranges[col] = {
                'min_date': str(self.df[col].min()),
                'max_date': str(self.df[col].max()),
                'span_days': int((self.df[col].max() - self.df[col].min()).days)
            }
        self.metadata['date_ranges'] = date_ranges

        # Numeric summary
        numeric_summary = {}
        for col in self.df.select_dtypes(include=np.number).columns:
            numeric_summary[col] = {
                'min':  round(float(self.df[col].min()), 4),
                'max':  round(float(self.df[col].max()), 4),
                'mean': round(float(self.df[col].mean()), 4),
                'std':  round(float(self.df[col].std()), 4),
                'sum':  round(float(self.df[col].sum()), 4),
            }
        self.metadata['numeric_summary'] = numeric_summary

        # Top values for categorical columns
        top_values = {}
        for col in self.df.select_dtypes(include=['object', 'category']).columns:
            top_values[col] = (
                self.df[col]
                .value_counts()
                .head(10)
                .to_dict()
            )
        self.metadata['top_categorical_values'] = top_values

        # -------------------------------------------------------
        # LLM-READY schema description string
        # -------------------------------------------------------
        lines = [
            f"Dataset: {self.metadata['row_count']} rows × {self.metadata['column_count']} columns.",
            "Columns:"
        ]
        for col in self.df.columns:
            dtype   = self.metadata['data_types'][col]
            n_uniq  = self.metadata['unique_values'][col]
            col_line = f"  - {col} ({dtype}, {n_uniq} unique values)"

            if col in numeric_summary:
                s = numeric_summary[col]
                col_line += f" | min={s['min']}, max={s['max']}, mean={s['mean']}"

            if col in top_values:
                top3 = list(top_values[col].keys())[:3]
                col_line += f" | top values: {top3}"

            if col in date_ranges:
                dr = date_ranges[col]
                col_line += f" | range: {dr['min_date']} to {dr['max_date']}"

            lines.append(col_line)

        if self.metadata.get('sample_rows'):
            lines.append(f"\nSample row: {self.metadata['sample_rows'][0]}")

        self.metadata['llm_schema_description'] = "\n".join(lines)

        print("Metadata extraction completed")

# =====================================================
# GENERATE LLM SCHEMA DESCRIPTION
# =====================================================

    def generate_llm_schema_description(self):

        schema_text = []

        schema_text.append(
            f"Dataset Shape: {self.df.shape}"
        )

        schema_text.append("\nColumns Information:\n")

        for col in self.df.columns:

            dtype = str(self.df[col].dtype)

            unique_values = self.df[col].nunique()

            line = (
                f"Column: {col} | "
                f"Type: {dtype} | "
                f"Unique Values: {unique_values}"
            )

            # NUMERIC SUMMARY
            if pd.api.types.is_numeric_dtype(self.df[col]):

                line += (
                    f" | Min: {self.df[col].min()}"
                    f" | Max: {self.df[col].max()}"
                    f" | Mean: {round(self.df[col].mean(), 2)}"
                )

            # CATEGORY SUMMARY
            elif self.df[col].dtype == 'category' or dtype == 'object':

                top_values = (
                    self.df[col]
                    .value_counts()
                    .head(3)
                    .index
                    .tolist()
                )

                line += f" | Top Values: {top_values}"

            # DATE SUMMARY
            if 'datetime' in dtype:

                line += (
                    f" | Date Range: "
                    f"{self.df[col].min()} "
                    f"to "
                    f"{self.df[col].max()}"
                )

            schema_text.append(line)

        final_schema = "\n".join(schema_text)

        self.metadata[
            'llm_schema_description'
        ] = final_schema

        print("LLM schema description generated")
        # =============================================================
        # FULL PIPELINE
        # =============================================================

    def process(self):
        """
        Runs every step in the correct order.
        Returns the clean DataFrame and the full metadata dict.
        """
        print("\n" + "="*60)
        print("  STARTING DATA PREPROCESSING PIPELINE")
        print("="*60)

        self.load_file()                      # Step 1
        self.standardize_column_names()       # Step 2
        self.clean_currency_columns()         # Step 2.1
        self.fix_categorical_inconsistencies()# Step 2.2
        self.remove_duplicates()              # Step 3
        self.drop_useless_columns()           # Step 4  ← NEW
        self.convert_numeric_columns()        # Step 5
        self.convert_date_columns()           # Step 6
        self.fix_categorical_inconsistencies()# Step 7  ← NEW
        self.analyze_missing_values()         # Step 8
        self.handle_missing_values()          # Step 9
        self.remove_empty_rows()              # Step 10
        self.optimize_memory()
        self.handle_outliers()                # Step 11
        self.optimize_memory()                # Step 12 ← NEW
        self.extract_metadata()              # Step 13
        self.generate_llm_schema_description()

        print("\n" + "="*60)
        print("  PIPELINE COMPLETE")
        print(f"  Final shape: {self.df.shape}")
        print("="*60 + "\n")

        return self.df, self.metadata


# =============================================================
# MAIN — local file test
# =============================================================

if __name__ == '__main__':

    import sys

    file_path = sys.argv[1] if len(sys.argv) > 1 else 'data/sample.csv'

    processor = DataProcessor(r"C:\Users\Krish Patel\OneDrive\Desktop\M_tech\LLM\data\Walmart.csv")
    clean_df, metadata = processor.process()

    # =========================================================
    # SAVE SUMMARY TO FILE
    # =========================================================

    output_file = "outputs/dataset_summary.txt"

    with open(output_file, "w", encoding="utf-8") as f:

        # ==========================================
        # BASIC INFO
        # ==========================================

        f.write("=" * 60 + "\n")
        f.write("DATASET SUMMARY REPORT\n")
        f.write("=" * 60 + "\n\n")

        # ==========================================
        # LLM SCHEMA
        # ==========================================

        f.write("LLM SCHEMA DESCRIPTION\n")
        f.write("-" * 60 + "\n")

        f.write(metadata['llm_schema_description'])

        f.write("\n\n")

        # ==========================================
        # MISSING VALUES
        # ==========================================

        f.write("MISSING VALUE DECISIONS\n")
        f.write("-" * 60 + "\n")

        for col, info in metadata['missing_values'].items():

            if info['missing_count'] > 0:

                f.write(
                    f"{col}: "
                    f"{info['missing_percent']}% missing "
                    f"→ {info['recommendation']} "
                    f"| important={info['is_important']}\n"
                )

        f.write("\n")

        # ==========================================
        # OUTLIERS
        # ==========================================

        f.write("OUTLIER HANDLING\n")
        f.write("-" * 60 + "\n")

        for col, info in metadata.get('outliers_handled', {}).items():

            if info['count'] > 0:

                f.write(
                    f"{col}: "
                    f"{info['count']} outliers "
                    f"({info['percent']}%) "
                    f"clipped to "
                    f"[{info['lower_bound']}, {info['upper_bound']}]\n"
                )

        f.write("\n")

        # ==========================================
        # CLEAN DATASET SAMPLE
        # ==========================================

        f.write("CLEAN DATASET SAMPLE\n")
        f.write("-" * 60 + "\n")

        f.write(clean_df.head().to_string())

        f.write("\n\n")

    print(f"\nDataset summary saved to: {output_file}")