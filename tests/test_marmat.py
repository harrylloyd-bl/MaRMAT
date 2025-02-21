import pytest
from pandas import read_csv
from marmat.audit import AuditTool


def test_init_attrs():
    tool = AuditTool()
    assert tool.lexicon_df is None
    assert tool.metadata_df is None
    assert tool.columns == []
    assert tool.categories == []
    assert tool.selected_columns == []
    assert tool.selected_categories == []
    assert tool.id_col is None


class TestMaRMAT:
    cols = [
        "System No [001]", "title", "description", "creator", "date",
        "collection name", "subjects", "spatial coverage"
    ]

    @pytest.fixture(scope="class")
    def tool(self):
        tool = AuditTool()
        tool.select_columns(["title"])  # Input the name(s) of the metadata column(s) you want to analyze.
        tool.select_identifier_column("System No [001]")
        tool.select_categories(["RaceTerms", "JapaneseincarcerationTerm"])
        with pytest.raises(ValueError):
            tool.load_metadata("tests/example-input-metadata.csv", id_col="System No [001]")
        tool.load_lexicon("tests/example-lexicon.csv")
        return tool

    def test_attrs(self, tool):
        assert tool.columns == []
        assert tool.id_col == "System No [001]"
        assert tool.categories == ["RaceTerms", "JapaneseincarcerationTerm"]
        assert tool.selected_columns == ["title"]
        assert tool.selected_categories == ["RaceTerms", "JapaneseincarcerationTerm"]
        assert tool.lexicon_df.dtypes["plural"] == bool

    def test_find_matches(self, tool, capsys):
        standard_cols = [tool.id_col, "Term", "Category", "Field", "FieldText",  "Occurences"]

        tool.load_metadata("tests/example-input-metadata.csv", id_col="System No [001]", allow_duplicate_ids=True)
        tool.select_columns(["title"])
        cat = ["RaceTerms"]
        tool.select_categories(cat)
        tool.audit_metadata()
        one_cat_df = tool.matches_df
        captured = capsys.readouterr()
        assert captured.out == f"\nProcessing term category: {cat[0]}\n"
        assert one_cat_df.shape == (4, 6)
        assert one_cat_df["System No [001]"].to_list() == [337805, 1302623, 1498946, 1533946]
        assert one_cat_df.loc[0, "Field"] == "title"
        assert one_cat_df.loc[0, "FieldText"] == "Aborigines of Taiwan [001]"
        assert one_cat_df.loc[1, "FieldText"] == "Busts of Ute Indians [1]"
        assert one_cat_df.loc[2, "FieldText"] == "Spanish at Indian pueblo"
        assert one_cat_df.loc[3, "FieldText"] == "Basalt-capped mesa on Dolores (Triassic), 6± miles south of Beddehoche (Indian Wells), Ariz., 1909 (photo G-67)"
        assert one_cat_df.columns.to_list() == standard_cols

        tool.select_columns(["title"])
        cats = ["RaceTerms", "JapaneseincarcerationTerm"]
        tool.select_categories(cats)
        tool.audit_metadata()
        two_cat_df = tool.matches_df
        captured = capsys.readouterr()
        assert captured.out == f"\nProcessing term category: {cats[0]}\n" \
                               f"\nProcessing term category: {cats[1]}\n"
        assert two_cat_df.shape == (7, 6)
        assert two_cat_df["System No [001]"].to_list() == [941496, 941536, 941713, 337805, 1302623, 1498946, 1533946]
        assert two_cat_df.loc[0, "FieldText"] == "Aborigines of Taiwan [001]"
        assert two_cat_df.loc[1, "FieldText"] == "Busts of Ute Indians [1]"
        assert two_cat_df.loc[5, "FieldText"] == "Evacuees cleaning vegetables in the packing shed."
        assert two_cat_df.loc[6, "FieldText"] == "Evacuees harvesting potatoes at Tule Lake. [5]"
        assert two_cat_df.columns.to_list() == standard_cols

        with pytest.warns(UserWarning):
            tool.select_columns(["title", "description"])
            cats = ["RaceTerms", "JapaneseincarcerationTerm"]
            tool.select_categories(cats)
            tool.audit_metadata()
        two_cat_two_col_df = tool.matches_df
        captured = capsys.readouterr()
        assert captured.out == f"\nProcessing term category: {cats[0]}\n" \
                               f"\nProcessing term category: {cats[1]}\n"
        assert two_cat_two_col_df.shape == (20, 6)
        assert two_cat_two_col_df["System No [001]"].to_list() == [
            941496, 941496, 941536, 941536, 941713, 941713, 941496, 941536, 941713, 337805, 962277, 995167, 995167,
            1302623, 1302623, 1396777, 1498946, 1498946, 1533946, 1533946
        ]

        assert two_cat_two_col_df.loc[0, "FieldText"] == "Aborigines of Taiwan [001]"
        assert two_cat_two_col_df.loc[5, "FieldText"] == "Photo taken at a court hearing or de-briefing following the American Indian Movement takeover at Wounded Knee, South Dakota, in 1973."
        assert two_cat_two_col_df.loc[16, "FieldText"] == "Photo of evacuees harvesting potatoes at the Tule Lake Relocation Center in California during World War II"
        assert two_cat_two_col_df.columns.to_list() == standard_cols
        assert two_cat_two_col_df.loc[10, "FieldText"][:53] == "The 14th Occasional paper of the University of Utah's"
        assert two_cat_two_col_df.loc[10, "Occurences"] == 4
        two_cat_two_col_df.to_csv("example-output.csv", encoding="utf8", index=False)

    def test_perform_matching(self, tool, tmp_path):
        blank_tool = AuditTool()
        with pytest.raises(ValueError):  # neither metadata nor lexicon
            blank_tool.audit_metadata()

        with pytest.raises(ValueError):  # lexicon but no metadata
            blank_tool.load_lexicon("tests/example-lexicon.csv")
            blank_tool.audit_metadata()

        tool.select_columns(["title", "description"])
        with pytest.warns(UserWarning):
            tool.audit_metadata()
        tool.export_matches(tmp_path / "test_output.csv")
        check_df = read_csv(tmp_path / "test_output.csv")
        assert check_df.shape == (20, 6)
