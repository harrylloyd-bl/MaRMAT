import os
from marmat.audit import AuditTool

LEXICON_PATH = "data\\external\\bl_lexicon_plural.csv"
INTERIM_PATH = "data\\interim\\"
PROCESSED_PATH = "data\\processed\\idcop\\"

ALEPH = True
IAMS = False

if __name__ == "__main__":

    record_files = {
        "aleph": [
            "epBooksPre1700", "epBooks1700s", "epBooks1800s_1", "epBooks1800s_2", "epBooks1800s_3",
            "epBooks1800s_4", "Maps", "Music"
        ],
        "iams": [
            "India Office_v2", "Map Collections_v2", "Music Collections_v2", "Oriental Manuscripts_v2",
            "Philatelic Collections_v2", "Printed Collections_v2", "Qatar_v2", "Sound Archive_v2",
            "Visual Arts_v2", "Western Manuscripts_v2"
        ]
    }

    print("Initialize")
    tool = AuditTool()

    print("Loading lexicon and metadata files")
    tool.load_lexicon(LEXICON_PATH)  # Input the path to your lexicon CSV file.

    # Aleph
    if ALEPH:
        print(f"Setting metadata, ID columns, and lexicon categories")
        tool.select_columns(["Title [245]"])  # Input the name(s) of the metadata column(s) you want to analyze.
        tool.select_categories(["Race", "Enslavement"])

        for f in record_files["aleph"][:1]:
            print(f"\nLoading {f}")
            tool.load_metadata(os.path.join(INTERIM_PATH, f"{f}.csv"), id_col="System No [001]")  # Input the path to your metadata CSV file
            tool.select_export_cols(tool.columns)

            print("Matching and exporting results")
            output_file = os.path.join(PROCESSED_PATH, f"{f}_matches.csv")  # Input the file path where you want to save your matches here.
            tool.audit_metadata()
            tool.export_matches(output_file)
        print("\nAleph files audit complete")

    #IAMS
    if IAMS:
        print(f"Setting metadata, ID columns, and lexicon categories")
        tool.select_columns(["Title", "Scope and content"])  # Input the name(s) of the metadata column(s) you want to analyze.
        tool.select_categories(["Race", "Enslavement", "Aggrandizement"])

        for f in record_files["iams"]:

            print(f"\nLoading {f}")
            tool.load_metadata(os.path.join(INTERIM_PATH, f"{f}.csv"), id_col="Record ID")  # Input the path to your metadata CSV file
            tool.select_export_cols(tool.columns)
            print("Matching and exporting results")
            output_file = os.path.join(PROCESSED_PATH, f"{f}_matches.csv")  # Input the file path where you want to save your matches here.
            tool.audit_metadata()
            tool.export_matches(output_file)

        print("IAMS files audit complete")
