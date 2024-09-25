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
        self.selected_columns = []  # List of columns selected for matching
        self.id_col = None  # Identifier column used to uniquely identify rows

    def load_lexicon(self, file_path):
        """Load the lexicon file.

        Parameters:
        file_path (str): Path to the lexicon CSV file.

        """
        try:
            self.lexicon_df = pd.read_csv(file_path, encoding='latin1')
            print("Lexicon loaded successfully.")
        except Exception as e:
            print(f"An error occurred while loading lexicon: {e}")

    def load_metadata(self, file_path):
        """Load the metadata file.

        Parameters:
        file_path (str): Path to the metadata CSV file.

        """
        try:
            self.metadata_df = pd.read_csv(file_path, encoding='latin1')
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
        self.categories = categories

    def perform_matching(self, output_file):
        """Perform matching between selected columns and categories and save results to a CSV file.

        Parameters:
        output_file (str): Path to the output CSV file to save matching results.

        """
        if self.lexicon_df is None or self.metadata_df is None:
            print("Please load lexicon and metadata files first.")
            return

        matches_df = self.find_matches(self.selected_columns, self.categories)
        matches_df.sort_values(by=["Category", "Term"], inplace=True)

        """Write results to CSV"""
        try:
            matches_df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"An error occurred while saving results: {e}")

    def find_matches(self, selected_columns, selected_categories):
        """Find matches between metadata and lexicon based on selected columns and categories.

        Parameters:
        selected_columns (list of str): List of column names from metadata for matching.
        selected_categories (list of str): List of category names from the lexicon for matching.

        Returns:
        list of tuple: List of tuples containing matched results (Identifier, Term, Category, Column).

        """
        lexicon_df = self.lexicon_df[self.lexicon_df['category'].isin(selected_categories)]
        cumsum = lexicon_df.groupby(by="category")["category"].count().cumsum().shift(1)
        cumsum.iloc[0] = 0
        cumsum = cumsum.astype(int)

        combined_dfs = []
        context_window = 30  # n_chars

        for i, (term, category) in enumerate(zip(lexicon_df['term'], lexicon_df['category'])):
            print(f"Processing {category} term {i + 1 - cumsum.loc[category]} of {len(lexicon_df.query('category == @category'))}")
            term_col_dfs = []
            bounded_term = re.compile(r"(?<=\b)" + f"({term})" + r"(?=\b)", flags=re.IGNORECASE)  # make term a group for .extract()

            for col in selected_columns:
                matches = self.metadata_df[self.metadata_df[col].str.contains(term, regex=False, na=False, case=False)]
                if len(matches) > 0:
                    matches = matches.copy()
                    # create elipsis padded context
                    split = matches[col].str.split(bounded_term, n=1, regex=True, expand=True).dropna()
                    if split.shape[1] == 1:
                        continue
                    start = split[0].str.slice(start=-context_window)
                    end = split[2].str.slice(stop=context_window)
                    start_pad = start.where(start.transform(len) != context_window, "..." + start)
                    end_pad = end.where(end.transform(len) != context_window, end + "...")
                    matches["Context (First Occurence)"] = start_pad + split[1] + end_pad

                    # add all other cols
                    matches["Term"] = term
                    matches["Category"] = category
                    matches["Field"] = col
                    matches["Occurences"] = matches[col].str.count(bounded_term)

                    term_col_dfs.append(matches.loc[:, (self.id_col, 'Term', 'Category', 'Context (First Occurence)', 'Field', 'Occurences')])

            if term_col_dfs:
                combined_dfs.append(pd.concat(term_col_dfs, axis=0))

        return pd.concat(combined_dfs, axis=0)


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
    tool.perform_matching(output_file)
