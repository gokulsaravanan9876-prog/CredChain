"""job marketplace: company profile fields, jobs, job applications, student skills

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-23 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


job_employment_type = sa.Enum('full_time', 'part_time', 'internship', 'contract', name='job_employment_type')
job_status = sa.Enum('draft', 'open', 'closed', name='job_status')
application_status = sa.Enum(
    'applied', 'under_review', 'shortlisted', 'rejected', 'accepted', 'withdrawn', name='application_status'
)


def upgrade() -> None:
    op.add_column('companies', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('location', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('company_size', sa.String(length=50), nullable=True))

    op.add_column('students', sa.Column('skills', postgresql.JSONB(), nullable=True))

    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('employment_type', job_employment_type, nullable=False),
        sa.Column('required_degree', sa.String(length=255), nullable=True),
        sa.Column('minimum_cgpa', sa.Numeric(4, 2), nullable=True),
        sa.Column('graduation_year_requirement', sa.Integer(), nullable=True),
        sa.Column('required_skills', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('required_certifications', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('required_documents', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('status', job_status, nullable=False, server_default='draft'),
        sa.Column('application_deadline', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_jobs_company_id', 'jobs', ['company_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_company_status', 'jobs', ['company_id', 'status'])

    op.create_table(
        'job_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', application_status, nullable=False, server_default='applied'),
        sa.Column('credential_request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('credential_requests.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_job_applications_student_id', 'job_applications', ['student_id'])
    op.create_index('ix_job_applications_job_id', 'job_applications', ['job_id'])
    op.create_index('ix_job_applications_company_id', 'job_applications', ['company_id'])
    op.create_index('ix_job_applications_status', 'job_applications', ['status'])
    op.create_index('ix_job_applications_student_status', 'job_applications', ['student_id', 'status'])
    op.create_index('ix_job_applications_company_status', 'job_applications', ['company_id', 'status'])


def downgrade() -> None:
    op.drop_index('ix_job_applications_company_status', table_name='job_applications')
    op.drop_index('ix_job_applications_student_status', table_name='job_applications')
    op.drop_index('ix_job_applications_status', table_name='job_applications')
    op.drop_index('ix_job_applications_company_id', table_name='job_applications')
    op.drop_index('ix_job_applications_job_id', table_name='job_applications')
    op.drop_index('ix_job_applications_student_id', table_name='job_applications')
    op.drop_table('job_applications')

    op.drop_index('ix_jobs_company_status', table_name='jobs')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_company_id', table_name='jobs')
    op.drop_table('jobs')

    op.drop_column('students', 'skills')

    op.drop_column('companies', 'company_size')
    op.drop_column('companies', 'location')
    op.drop_column('companies', 'description')

    application_status.drop(op.get_bind(), checkfirst=True)
    job_status.drop(op.get_bind(), checkfirst=True)
    job_employment_type.drop(op.get_bind(), checkfirst=True)
