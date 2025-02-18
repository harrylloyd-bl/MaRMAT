from collections import defaultdict
import re
import warnings
import pandas as pd
from tqdm import tqdm


class AuditTool:
    """A tool for assessing metadata and identifying matches based on a provided lexicon."""

    def __init__(self):
        """Initialize the assessment tool."""
        self.lexicon_df = None
        self.metadata_df = None
        self.columns = []  # List of all available columns in the metadata
        self.categories = []  # List of all available categories in the lexicon
        self.selected_columns = []  # List of columns selected for matching
        self.selected_categories = []  # List of categories selected for matching
        self.id_col = None  # Identifier column used to uniquely identify rows
        self.export_cols = []
        self.matches_df = None

    def load_lexicon(self, file_path):
        """Load the lexicon file.

        Parameters:
        file_path (str): Path to the lexicon CSV file.

        """
        try:
            self.lexicon_df = pd.read_csv(file_path, encoding='utf8')
            if "plural" in self.lexicon_df.columns and self.lexicon_df.dtypes["plural"] != bool:
                raise TypeError(f"Plural dtype is {self.lexicon_df.dtypes['plural']} not bool")
            self.categories = self.lexicon_df["category"].unique().tolist()
            print("Lexicon loaded successfully.")
        except Exception as e:
            raise Exception(f"An error occurred while loading lexicon: {e}")

    def default_str(self):
        return str

    def load_metadata(self, file_path, id_col, allow_duplicate_ids=False):
        """Load the metadata file.

        Parameters:
        file_path (str): Path to the metadata CSV file.

        """
        try:
            dtypes = defaultdict(self.default_str)
            dtypes["System No [001]"] = pd.Int64Dtype()
            df = pd.read_csv(file_path, encoding='utf8', dtype=dtypes)
        except Exception as e:
            raise Exception(f"An error occurred while loading metadata: {e}")

        if not allow_duplicate_ids and not df[id_col].is_unique:
            raise ValueError(
                f"{id_col} in Metadata is not unique. Make unique or set allow_duplicate_ids=True. "
                f"This will lead to duplicate results in ouput.")

        self.metadata_df = df
        self.columns = self.metadata_df.columns.to_list()
        self.id_col = id_col
        print("Metadata loaded successfully.")


    def select_columns(self, columns):
        """Select columns from the metadata for matching.

        Parameters:
        columns (list of str): List of column names in the metadata.

        """
        self.selected_columns = columns

    def select_identifier_column(self, column):
        """Select the identifier column used for uniquely identifying rows.

        Parameters:
        column (str): Name of the identifier column in the metadata.

        """
        self.id_col = column

    def select_categories(self, categories):
        """Select categories from the lexicon for matching.

        Parameters:
        categories (list of str): List of category names in the lexicon.

        """
        self.selected_categories = categories

    def select_export_cols(self, export_cols):
        """Select categories from the lexicon for matching.

        Parameters:
        export_cols (list of str): List of column names in metadata_df to export.

        """
        self.export_cols = export_cols

    def perform_matching(self):
        """Perform matching between selected columns and categories and save results to a CSV file.

        Parameters:
        output_file (str): Path to the output CSV file to save matching results.

        """
        if self.lexicon_df is None or self.metadata_df is None:
            raise ValueError("Please load lexicon and metadata files first.")
        elif set(self.selected_categories) - set(self.categories):
            missing_cats = set(self.selected_categories) - set(self.categories)
            raise ValueError(f"{missing_cats} not in lexicon categories")
        elif set(self.selected_columns) - set(self.columns):
            missing_cols = set(self.selected_columns) - set(self.columns)
            raise ValueError(f"{missing_cols} not in metadata columns")

        if not (self.metadata_df is not None and self.lexicon_df is not None):
            raise ValueError("Please load lexicon and metadata files first.")

        self.matches_df = self.find_matches(self.selected_columns, self.selected_categories)
        self.matches_df.sort_values(by=["Category", "Term", self.id_col], inplace=True)
        duplicate_check = self.matches_df.groupby(by=["Category", "Term", "Field", self.id_col])["Occurences"].count()
        if duplicate_check.max() > 1:
            n = duplicate_check.sum() - duplicate_check.shape[0]
            warnings.warn(f"{n} duplicate rows in output, check uniqueness of ID field in input.")
        return None

    def find_matches(self, selected_columns, selected_categories):
        """Find matches between metadata and lexicon based on selected columns and categories.

        Parameters:
        selected_columns (list of str): List of column names from metadata for matching.
        selected_categories (list of str): List of category names from the lexicon for matching.

        Returns:
        list of tuple: List of tuples containing matched results (Identifier, Term, Category, Column).

        """
        lexicon_df = self.lexicon_df[self.lexicon_df['category'].isin(selected_categories)].copy()
        lexicon_df.sort_values(by="category",  # sort lexicon to same order as selected_categories
                               key=lambda x: x.map({k: i for i, k in enumerate(selected_categories)}),
                               inplace=True)

        combined_dfs = []

        for category, grp in lexicon_df.groupby(by="category", sort=False):
            print(f"Processing term category: {category}")
            for _, (term, _, plural) in tqdm(grp.iterrows(), total=len(grp)):
                # print(f"Processing {category} term {i + 1 - cumsum.loc[category]} of {count.loc[category]}")
                term_col_dfs = []
                if plural:
                    bounded_term = re.compile(r"(?<=\b)" + f"({term}s?)" + r"(?=\b)", flags=re.IGNORECASE)  # make term a group for .split()
                else:
                    bounded_term = re.compile(r"(?<=\b)" + f"({term})" + r"(?=\b)", flags=re.IGNORECASE)  # make term a group for .split()

                for col in selected_columns:
                    raw_matches = self.metadata_df[self.metadata_df[col].str.contains(term, regex=False, na=False, case=False)]
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        matches = raw_matches[raw_matches[col].str.contains(bounded_term, regex=True, na=False)].copy()
                    if len(matches) > 0:
                        matches.rename(columns={col: "Context"}, inplace=True)

                        # add all other cols
                        matches["Term"] = term
                        matches["Category"] = category
                        matches["Field"] = col
                        matches["Occurences"] = matches["Context"].str.count(bounded_term)

                        standard_cols = [self.id_col, 'Term', 'Category', 'Context', 'Field', 'Occurences']
                        term_col_dfs.append(matches.loc[:, standard_cols + self.export_cols])

                if term_col_dfs:
                    combined_dfs.append(pd.concat(term_col_dfs, axis=0))

        matches_df = pd.concat(combined_dfs, axis=0).reset_index(drop=True)
        return matches_df

    def export_matches(self, output_file):
        """
        Write results to CSV
        Parameters:
        output_file (str): Path to the output CSV file to save matching results.
        """
        try:
            self.matches_df.to_csv(output_file, index=False, encoding="utf8")
            output_file = str(output_file)
            self.matches_df.to_excel(output_file.replace(".csv", ".xlsx"), index=False)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"An error occurred while saving results: {e}")
