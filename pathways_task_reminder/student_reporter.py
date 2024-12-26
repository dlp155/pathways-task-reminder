import dataclasses
import tempfile
from pathlib import Path

import pandas as pd

from pathways_task_reminder import constants as const
from pathways_task_reminder.pdf_table_parser import PDFTableParser
from pathways_task_reminder.utils.dataframe import to_table
from pathways_task_reminder.utils.html import to_image_path as html_path_to_png_path


@dataclasses.dataclass
class StudentReport:
    ASSIGNMENT_INDEX = "week"
    ASSIGNMENT_VALUES = "units"

    LEVEL = "level"
    UNITS = "units"
    SKILL_INDEX = [LEVEL, UNITS]
    SKILL_VALUES = "skill"
    MEAN_UNITS_TEXT = "Avg units completed e/ wk of semester"

    # If not present keeps current name
    SKILL_DISPLAY = {
        "grammar": "gram",
        "vocabulary": "vocab",
    }

    name: str
    skill_df: pd.DataFrame
    assignment_series: pd.Series

    def to_html(self):
        assignment_df = self.assignment_series.to_frame(name=self.ASSIGNMENT_VALUES).T
        mean_units_per_week = self.mean_units_per_week()
        skill_df_wo_level = self.skill_df.drop(self.LEVEL, axis=0)
        skill_df = skill_df_wo_level.rename(columns=self.SKILL_DISPLAY)
        parts = [
            self._create_styling(),
            "<br/>",
            to_table(assignment_df),
            "<br/>",
            to_table(skill_df),
            self._create_paragraph(
                f"{self.MEAN_UNITS_TEXT}: {mean_units_per_week:.1f}"
            ),
        ]
        return "\n".join(parts)

    @staticmethod
    def _create_paragraph(text):
        return f"<p>{text}</p>"

    def _create_styling(self):
        style_block = """<style>
        table, th, td {
            border: 1px solid #d3d3d3;
            border-collapse: collapse;
            font-family: Arial, Helvetica, sans-serif;
        }
        th {
            text-align: center;
            padding: 6px;
            background-color: #f9f9f9;
        }
        td {
            text-align: left;
            padding: 5px;
        }
        p {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 90%;
        }
        </style>\n"""
        return style_block

    def to_image(self):
        html = self.to_html()
        try:
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html:
                temp_html.write(html.encode("utf8"))
                html_path = Path(
                    temp_html.name
                )  # Get the full path of the temporary HTML file

            png_path = html_path.with_suffix(".png")
            html_path_to_png_path(html_path, png_path)
        finally:
            Path(html_path).unlink(missing_ok=True)

        return png_path

    def mean_units_per_week(self):
        return self.assignment_series.fillna(0).mean()


class StudentReporter:
    @classmethod
    def create_images_from_pdf(cls, pdf_path) -> dict[str, Path]:
        tables = PDFTableParser().extract_tables(pdf_path)
        return cls().create_student_report_images(tables)

    def create_student_report_images(self, tables):
        student_reports = self.create_student_reports(tables)
        return {report.name: report.to_image() for report in student_reports}

    def create_student_reports(self, tables):
        student_series = self._create_student_series(tables)
        return self._create_student_reports_from_series(student_series)

    def _create_student_series(self, tables):
        return {key: self._extract_students(df) for key, df in tables.items()}

    @staticmethod
    def _extract_students(df):
        """Returns a list of student series."""
        return {
            row[0]: pd.Series(row[1:], index=df.columns[1:])
            for row in df.itertuples(index=False)
        }

    def _create_student_reports_from_series(self, student_series_by_table_name):
        student_names = student_series_by_table_name[
            const.STUDENT_LEVEL_BY_SKILL
        ].keys()
        return [
            self._assemble_student(name, student_series_by_table_name)
            for name in student_names
        ]

    def _assemble_student(self, name, student_series):
        skill_levels = student_series[const.STUDENT_LEVEL_BY_SKILL][name]
        skill_nums = student_series[const.TOTAL_ASSIGNMENTS_BY_SKILL][name]

        skill_df = pd.DataFrame(
            [skill_levels, skill_nums], index=StudentReport.SKILL_INDEX
        )
        skill_df.columns.name = StudentReport.SKILL_VALUES
        assignment_series = student_series[const.ASSIGNMENTS_SUBMITTED_BY_WEEK][name]
        assignment_series.index.name = StudentReport.ASSIGNMENT_INDEX
        return StudentReport(
            name=name, skill_df=skill_df, assignment_series=assignment_series
        )
