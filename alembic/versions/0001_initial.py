"""Initial PreventVital tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("sex", sa.String(16), nullable=False),
        sa.Column("height_cm", sa.Float()),
        sa.Column("weight_kg", sa.Float()),
        sa.Column("waist_cm", sa.Float()),
        sa.Column("smoking", sa.String(32), server_default="never"),
        sa.Column("cigs_per_day", sa.Float()),
        sa.Column("alcohol", sa.String(32), server_default="none"),
        sa.Column("activity_level", sa.String(32), server_default="moderate"),
        sa.Column("diet_quality", sa.String(32), server_default="average"),
        sa.Column("stress_level", sa.Integer()),
        sa.Column("family_hx_diabetes", sa.String(32), server_default="none"),
        sa.Column("family_hx_cvd", sa.Boolean(), server_default=sa.false()),
        sa.Column("bp_meds", sa.Boolean(), server_default=sa.false()),
        sa.Column("existing_hypertension", sa.Boolean(), server_default=sa.false()),
        sa.Column("existing_diabetes", sa.Boolean(), server_default=sa.false()),
        sa.Column("prior_stroke", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "clinical_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), index=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sys_bp", sa.Float()),
        sa.Column("dia_bp", sa.Float()),
        sa.Column("fasting_glucose", sa.Float()),
        sa.Column("hba1c", sa.Float()),
        sa.Column("total_chol", sa.Float()),
        sa.Column("hdl", sa.Float()),
        sa.Column("ldl", sa.Float()),
        sa.Column("triglycerides", sa.Float()),
    )
    op.create_table(
        "wearable_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), index=True),
        sa.Column("date", sa.Date(), index=True),
        sa.Column("steps", sa.Float()),
        sa.Column("active_min", sa.Float()),
        sa.Column("calories", sa.Float()),
        sa.Column("rhr", sa.Float()),
        sa.Column("avg_hr", sa.Float()),
        sa.Column("max_hr", sa.Float()),
        sa.Column("hrv_rmssd", sa.Float()),
        sa.Column("spo2_avg", sa.Float()),
        sa.Column("spo2_min", sa.Float()),
        sa.Column("sleep_hours", sa.Float()),
        sa.Column("deep_pct", sa.Float()),
        sa.Column("rem_pct", sa.Float()),
        sa.Column("light_pct", sa.Float()),
        sa.Column("sleep_efficiency", sa.Float()),
        sa.Column("skin_temp_dev", sa.Float()),
        sa.Column("resp_rate", sa.Float()),
    )
    op.create_table(
        "risk_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), index=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("disease", sa.String(32)),
        sa.Column("baseline", sa.Float()),
        sa.Column("wearable_score", sa.Float()),
        sa.Column("composite", sa.Float()),
        sa.Column("ci_low", sa.Float()),
        sa.Column("ci_high", sa.Float()),
        sa.Column("band", sa.String(16)),
        sa.Column("top_factors_json", sa.JSON()),
        sa.Column("model_version", sa.String(64), server_default="untrained"),
    )
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id"), index=True),
        sa.Column("role", sa.String(16)),
        sa.Column("content", sa.Text()),
        sa.Column("tools_used_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("risk_reports")
    op.drop_table("wearable_daily")
    op.drop_table("clinical_records")
    op.drop_table("patients")
