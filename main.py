from Code.MaRMAT import MaRMAT

if __name__ == "__main__":
    print("1. Initialize the tool:")
    tool = MaRMAT()

    print("\n2. Load lexicon and metadata files:")
    tool.load_lexicon("data\\external\\reparative-metadata-lexicon.csv")  # Input the path to your lexicon CSV file.
    tool.load_metadata("data\\interim\\epBooksPre1700.csv")  # Input the path to your metadata CSV file.

    print("\n3. Select columns for matching:")
    tool.select_columns(["Title [245]"])  # Input the name(s) of the metadata column(s) you want to analyze.

    print("\n4. Select the identifier column:")
    tool.select_identifier_column("System No [001]")  # Input the name of your identifier column (e.g., a record ID number).

    print("\n5. Select categories for matching:")
    tool.select_categories(["SlaveryTerms", "RaceTerms", "RaceEuphemisms"])  # Input the categories from the lexicon that you want to search for.
    # tool.select_categories(["Disability", "GenderTerms", "LGBTQ", "MentalIllness", "RaceTerms", "RaceEuphemisms", "SlaveryTerms", "JapaneseincarcerationTerm", "Aggrandizement"])  # Input the categories from the lexicon that you want to search for.

    print("\n6. Perform matching and view results:")
    output_file = "data\\processed\\matches.csv"  # Input the file path where you want to save your matches here.
    tool.perform_matching(output_file)