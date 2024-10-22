import re
import pandas as pd


class MaRMAT:
    """A tool for assessing metadata and identifying matches based on a provided lexicon."""

    def __init__(self):
        """Initialize the assessment tool."""
        self.lexicon_df = None
        self.metadata_df = None
        self.columns = []  # List of all available columns in the metadata
        self.categories = []  # List of all available categories in the lexicon
        self.selected_categories = []  # List of all available categories in the lexicon
        self.selected_columns = []  # List of columns selected for matching
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
            self.categories = self.lexicon_df["category"].unique().tolist()
            print("Lexicon loaded successfully.")
        except Exception as e:
            print(f"An error occurred while loading lexicon: {e}")

    def load_metadata(self, file_path):
        """Load the metadata file.

        Parameters:
        file_path (str): Path to the metadata CSV file.

        """
        try:
            self.metadata_df = pd.read_csv(file_path, encoding='utf8')
            self.columns = self.metadata_df.columns.to_list()
            print("Metadata loaded successfully.")
        except Exception as e:
            print(f"An error occurred while loading metadata: {e}")

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
        """
        if self.lexicon_df is None or self.metadata_df is None:
            raise ValueError("Please load lexicon and metadata files first.")
        elif set(self.selected_categories) - set(self.categories):
            missing_cats = set(self.selected_categories) - set(self.categories)
            raise ValueError(f"{missing_cats} not in lexicon categories")
        elif set(self.selected_columns) - set(self.columns):
            missing_cols = set(self.selected_columns) - set(self.columns)
            raise ValueError(f"{missing_cols} not in metadata columns")

        self.matches_df = self.find_matches(self.selected_columns, self.selected_categories)
        self.matches_df.sort_values(by=["Category", "Term"], inplace=True)

    def find_matches(self, selected_columns, selected_categories):
        """Find matches between metadata and lexicon based on selected columns and categories.

        Parameters:
        selected_columns (list of str): List of column names from metadata for matching.
        selected_categories (list of str): List of category names from the lexicon for matching.

        Returns:
        list of tuple: List of tuples containing matched results (Identifier, Term, Category, Column).

        """
        lexicon_df = self.lexicon_df[self.lexicon_df['category'].isin(selected_categories)]
        count = lexicon_df.groupby(by="category", sort=False)["category"].count()
        cumsum = lexicon_df.groupby(by="category", sort=False)["category"].count().cumsum().shift(1)
        cumsum.iloc[0] = 0
        cumsum = cumsum.astype(int)

        combined_dfs = []
        context_window = 30  # n_chars

        for i, (term, category, plural) in enumerate(zip(lexicon_df['term'], lexicon_df['category'], lexicon_df['plural'])):
            print(f"Processing {category} term {i + 1 - cumsum.loc[category]} of {count.loc[category]}")
            term_col_dfs = []
            if plural:
                bounded_term = re.compile(r"(?<=\b)" + f"({term}s?)" + r"(?=\b)", flags=re.IGNORECASE)  # make term a group for .split()
            else:
                bounded_term = re.compile(r"(?<=\b)" + f"({term})" + r"(?=\b)", flags=re.IGNORECASE)  # make term a group for .split()

            for col in selected_columns:
                unbounded_matches = self.metadata_df[self.metadata_df[col].str.contains(term, regex=False, na=False, case=False)]
                if len(unbounded_matches) > 0:
                    # create elipsis padded context
                    split = unbounded_matches[col].str.split(bounded_term, n=1, regex=True, expand=True).dropna()
                    if split.shape[1] == 1:
                        continue
                    start = split[0].str.slice(start=-context_window)
                    end = split[2].str.slice(stop=context_window)
                    start_pad = start.where(start.transform(len) != context_window, "..." + start)
                    end_pad = end.where(end.transform(len) != context_window, end + "...")

                    matches = unbounded_matches.loc[split.index, [self.id_col, col] + self.export_cols]
                    matches["Context (First Occurence)"] = start_pad + split[1] + end_pad

                    # add all other cols
                    matches["Term"] = term
                    matches["Category"] = category
                    matches["Field"] = col
                    matches["Occurences"] = matches[col].str.count(bounded_term)

                    standard_cols = [self.id_col, 'Term', 'Category', 'Context (First Occurence)', 'Field', 'Occurences']
                    term_col_dfs.append(matches.loc[:, standard_cols + self.export_cols])

            if term_col_dfs:
                combined_dfs.append(pd.concat(term_col_dfs, axis=0))

        return pd.concat(combined_dfs, axis=0).reset_index(drop=True)

    def export_matches(self, output_file):
        """
        Write results to CSV
        Parameters:
        output_file (str): Path to the output CSV file to save matching results.
        """
        try:
            self.matches_df.to_csv(output_file, index=False, encoding="utf8")
            self.matches_df.to_excel(output_file.replace(".csv", ".xlsx"), index=False)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"An error occurred while saving results: {e}")


if __name__ == "__main__":
    # Define output file path
    output_file = "matches.csv"  # Input the file path where you want to save your matches here.

    # Example usage:
    print("1. Initialize the tool:")
    tool = MaRMAT()

    print("\n2. Load lexicon and metadata files:")
    tool.load_lexicon("lexicon.csv")  # Input the path to your lexicon CSV file.
    tool.load_metadata("metadata.csv")  # Input the path to your metadata CSV file.

    print("\n3. Select columns for matching:")
    tool.select_columns(["Column1", "Column2"])  # Input the name(s) of the metadata column(s) you want to analyze.

    print("\n4. Select the identifier column:")
    tool.select_identifier_column("Identifier")  # Input the name of your identifier column (e.g., a record ID number).

    print("\n5. Select categories for matching:")
    tool.select_categories(["RaceTerms"])  # Input the categories from the lexicon that you want to search for.

    print("\n6. Perform matching and view results:")
    tool.perform_matching()
    tool.export_matches(output_file)
