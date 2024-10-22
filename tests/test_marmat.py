import pytest
from pandas import read_csv
from Code.MaRMAT import MaRMAT


def test_col_cat_attrs():
    tool = MaRMAT()
    assert tool.columns == []
    assert tool.categories == []


@pytest.fixture(scope="module")
def m_tool():
    tool = MaRMAT()
    tool.load_lexicon("tests/lexicon_testing.csv")
    return tool


class TestAlephMaRMAT:
    cols = [
        "System No [001]", "008 Date1", "Nat Bib No [015]", "Dewey [082]", "Personal Name [100]", "Corp Name [110]",
        "Title [245]", "Statement Resp [245$c]", "Edition [250]", "Place Pub [260 and 264$a]",
        "Publisher [260 and 264$b]", "Date Pub [260 and 264$c]", "Phys Descr [300]", "Content Type [336]",
        "Media Type [337]", "Series [490]", "Cit note [510]", "Add Entry Name [700]", "Add Entry Corp Name [710]",
        "Place Name [752]", "Shelfmark [852]", "ALL AUTHS", "852NORMALIZED", "ALL PLACES", "ALL DATES"
    ]

    @pytest.fixture(scope="class")
    def tool(self, m_tool):
        tool = m_tool
        tool.select_columns(["Title [245]"])  # Input the name(s) of the metadata column(s) you want to analyze.
        tool.select_identifier_column("System No [001]")
        tool.select_categories(["Test_Cat_One", "Test_Cat_Two"])
        tool.select_export_cols(["Personal Name [100]", "Corp Name [110]", "Date Pub [260 and 264$c]", "Shelfmark [852]"])
        tool.load_metadata("tests/aleph_record_testing.csv")
        return tool

    def test_attrs(self, tool):
        assert tool.columns == self.cols
        assert tool.id_col == "System No [001]"
        assert tool.categories == ["Test_Cat_One", "Test_Cat_Two"]
        assert tool.selected_columns == ["Title [245]"]
        assert tool.selected_categories == ["Test_Cat_One", "Test_Cat_Two"]
        assert tool.export_cols == ["Personal Name [100]", "Corp Name [110]", "Date Pub [260 and 264$c]", "Shelfmark [852]"]

    def test_find_matches(self, tool, capsys):
        one_cat_df = tool.find_matches(selected_columns=["Title [245]"], selected_categories=["Test_Cat_One"])
        captured = capsys.readouterr()
        assert captured.out == "Processing Test_Cat_One term 1 of 1\n"
        assert one_cat_df.shape == (4, 6 + len(tool.export_cols))
        assert one_cat_df["System No [001]"].to_list() == [12957554, 12957555, 12957556, 12957557]
        assert one_cat_df.loc[0, "Field"] == "Title [245]"
        assert one_cat_df.loc[0, "Context (First Occurence)"] == "Effects based warfare / test_word_one "
        assert one_cat_df.loc[1, "Context (First Occurence)"] == "Effects based warfare / Test_word_one "
        assert one_cat_df.loc[2, "Context (First Occurence)"] == "Effects based warfare / test_word_ones and"
        assert one_cat_df.loc[3, "Context (First Occurence)"] == "Effects based warfare / Test_word_ones "
        standard_cols = [tool.id_col, 'Term', 'Category', 'Context (First Occurence)', 'Field', 'Occurences']
        assert one_cat_df.columns.to_list() == standard_cols + tool.export_cols

        two_cat_df = tool.find_matches(selected_columns=["Title [245]"], selected_categories=["Test_Cat_One", "Test_Cat_Two"])
        captured = capsys.readouterr()
        assert captured.out == "Processing Test_Cat_One term 1 of 1\nProcessing Test_Cat_Two term 1 of 1\n"
        assert two_cat_df.shape == (7, 6 + len(tool.export_cols))
        assert two_cat_df["System No [001]"].to_list() == [12957554, 12957555, 12957556, 12957557, 13020954, 13204315, 13204488]
        print(two_cat_df.loc[0, "Context (First Occurence)"])
        assert two_cat_df.loc[0, "Context (First Occurence)"] == "Effects based warfare / test_word_one "
        assert two_cat_df.loc[5, "Context (First Occurence)"] == "Test_word_two Lagrimas, faiscas do amor div..."
        assert two_cat_df.loc[6, "Context (First Occurence)"] == "...o, tremores da terra, e luzes test_word_two para a orac?am. Luzes golpes ..."
        standard_cols = [tool.id_col, 'Term', 'Category', 'Context (First Occurence)', 'Field', 'Occurences']
        assert two_cat_df.columns.to_list() == standard_cols + tool.export_cols

    def test_perform_matching(self, tool):
        tool.select_categories(["Non_Existent_Cat"])
        with pytest.raises(ValueError):
            tool.perform_matching()
        tool.select_categories(["Test_Cat_One", "Test_Cat_Two"])

        tool.select_columns(["Non_Existent_Col"])
        with pytest.raises(ValueError):
            tool.perform_matching()
        tool.select_columns(["Title [245]"])

        tool.perform_matching()
        assert tool.matches_df.shape == (7, 6 + len(tool.export_cols))

    def test_export_matches(self, tool, tmp_path):
        tool.perform_matching()
        tool.export_matches(tmp_path / "test_out.csv")
        reimport_df = read_csv(tmp_path / "test_out.csv")
        assert reimport_df.shape == (7, 6 + len(tool.export_cols))  # no index added during export


class TestIAMSMaRMAT:
    cols = [
        'Record ID', 'Hierarchy', 'Collection area', 'Project collections', 'Reference', 'Former internal reference',
        'Former external reference', 'MDARK', 'URL', 'Type of record', 'Parent', 'Sibling order', 'Title',
        'Additional titles', 'Date range', 'Start date', 'End date', 'Calendar', 'Era', 'Creators', 'Extent',
        'Languages', 'Scripts', 'Scope and content', 'Material type', 'Physical characteristics', 'Scale',
        'Scale designator', 'Projection', 'Decimal coordinates', 'Degree coordinates', 'Orientation',
        'Source of acquisition', 'Custodial history', 'Appraisal', 'Arrangement', 'Administrative context',
        'Information about copies', 'Information about originals', 'Publications about described materials',
        'Notes', 'Related material', 'Related Archive Descriptions', 'Related names', 'Related subjects',
        'Restrictions on access', 'Restrictions on use', 'Legal status'
    ]

    @pytest.fixture(scope="class")
    def tool(self, m_tool):
        tool = m_tool
        tool.select_identifier_column("Reference")
        tool.select_columns(["Title", "Scope and content"])  # Input the name(s) of the metadata column(s) you want to analyze.
        tool.select_categories(["Test_Cat_One", "Test_Cat_Two"])
        tool.select_export_cols(["Date range"])
        tool.load_metadata("tests/iams_record_testing.csv")
        return tool

    def test_attrs(self, tool):
        assert tool.columns == self.cols
        assert tool.id_col == "Reference"
        assert tool.categories == ["Test_Cat_One", "Test_Cat_Two"]
        assert tool.selected_columns == ["Title", "Scope and content"]
        assert tool.selected_categories == ["Test_Cat_One", "Test_Cat_Two"]
        assert tool.export_cols == ["Date range"]

    # Tested most elements of find_matches in TestAlephMaRMAT
    # Still need to test searching on more than one column
    def test_find_matches(self, tool, capsys):
        one_col_df = tool.find_matches(selected_columns=["Title"], selected_categories=["Test_Cat_One", "Test_Cat_Two"])
        captured = capsys.readouterr()
        assert captured.out == "Processing Test_Cat_One term 1 of 1\nProcessing Test_Cat_Two term 1 of 1\n"
        assert one_col_df.shape == (1, 6 + len(tool.export_cols))
        assert one_col_df["Reference"].to_list() == ["Imago Mundi"]
        assert one_col_df.loc[0, "Context (First Occurence)"] == "The Imago Mundi Archives test_word_one"
        standard_cols = [tool.id_col, 'Term', 'Category', 'Context (First Occurence)', 'Field', 'Occurences']
        assert one_col_df.columns.to_list() == standard_cols + tool.export_cols

        two_col_df = tool.find_matches(selected_columns=["Title", "Scope and content"], selected_categories=["Test_Cat_One", "Test_Cat_Two"])
        captured = capsys.readouterr()
        assert captured.out == "Processing Test_Cat_One term 1 of 1\nProcessing Test_Cat_Two term 1 of 1\n"
        assert two_col_df.shape == (2, 6 + len(tool.export_cols))
        assert two_col_df["Reference"].to_list() == ["Imago Mundi", "Imago Mundi MS 1"]
        assert two_col_df.loc[0, "Field"] == "Title"
        assert two_col_df.loc[1, "Field"] == "Scope and content"
        assert two_col_df.loc[0, "Context (First Occurence)"] == "The Imago Mundi Archives test_word_one"
        assert two_col_df.loc[1, "Context (First Occurence)"] == "1. WED Allen. test_word_two 1952-7; 2. Roberto Almagià. 1..."
