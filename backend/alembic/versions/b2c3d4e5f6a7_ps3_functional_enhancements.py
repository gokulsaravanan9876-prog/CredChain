"""PS3 functional enhancements: bulk issuance support, institution certificate
requests, student-uploaded documents, requested-vs-received verification,
view/download share permissions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-22 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


credential_type = postgresql.ENUM(
    'degree', 'transcript', 'migration', 'internship', 'certification', 'course', 'other',
    name='credential_type', create_type=False,
)
institution_request_status = sa.Enum(
    'pending', 'approved', 'rejected', 'fulfilled', name='institution_request_status'
)
student_document_status = sa.Enum(
    'unverified', 'under_review', 'approved', 'rejected', name='student_document_status'
)


def upgrade() -> None:
    # New enum values on existing native enum types must run outside a transaction.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE share_permission ADD VALUE IF NOT EXISTS 'view_download'")
        op.execute("ALTER TYPE verification_result_status ADD VALUE IF NOT EXISTS 'TYPE_MISMATCH'")

    op.create_table(
        'institution_certificate_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('credential_type', credential_type, nullable=False),
        sa.Column('custom_credential_name', sa.String(length=255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', institution_request_status, nullable=False, server_default='pending'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fulfilled_credential_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('credentials.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_institution_certificate_requests_student_id', 'institution_certificate_requests', ['student_id'])
    op.create_index('ix_institution_certificate_requests_institution_id', 'institution_certificate_requests', ['institution_id'])
    op.create_index('ix_institution_certificate_requests_status', 'institution_certificate_requests', ['status'])
    op.create_index('ix_institution_certificate_requests_student_status', 'institution_certificate_requests', ['student_id', 'status'])
    op.create_index('ix_institution_certificate_requests_institution_status', 'institution_certificate_requests', ['institution_id', 'status'])

    op.create_table(
        'student_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('credential_type', credential_type, nullable=False),
        sa.Column('custom_credential_name', sa.String(length=255), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('status', student_document_status, nullable=False, server_default='unverified'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resulting_credential_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('credentials.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_student_documents_student_id', 'student_documents', ['student_id'])
    op.create_index('ix_student_documents_institution_id', 'student_documents', ['institution_id'])
    op.create_index('ix_student_documents_status', 'student_documents', ['status'])
    op.create_index('ix_student_documents_content_hash', 'student_documents', ['content_hash'])
    op.create_index('ix_student_documents_student_status', 'student_documents', ['student_id', 'status'])
    op.create_index('ix_student_documents_institution_status', 'student_documents', ['institution_id', 'status'])

    op.add_column(
        'share_grants',
        sa.Column('credential_request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('credential_requests.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_share_grants_credential_request_id', 'share_grants', ['credential_request_id'])


def downgrade() -> None:
    op.drop_index('ix_share_grants_credential_request_id', table_name='share_grants')
    op.drop_column('share_grants', 'credential_request_id')

    op.drop_index('ix_student_documents_institution_status', table_name='student_documents')
    op.drop_index('ix_student_documents_student_status', table_name='student_documents')
    op.drop_index('ix_student_documents_content_hash', table_name='student_documents')
    op.drop_index('ix_student_documents_status', table_name='student_documents')
    op.drop_index('ix_student_documents_institution_id', table_name='student_documents')
    op.drop_index('ix_student_documents_student_id', table_name='student_documents')
    op.drop_table('student_documents')

    op.drop_index('ix_institution_certificate_requests_institution_status', table_name='institution_certificate_requests')
    op.drop_index('ix_institution_certificate_requests_student_status', table_name='institution_certificate_requests')
    op.drop_index('ix_institution_certificate_requests_status', table_name='institution_certificate_requests')
    op.drop_index('ix_institution_certificate_requests_institution_id', table_name='institution_certificate_requests')
    op.drop_index('ix_institution_certificate_requests_student_id', table_name='institution_certificate_requests')
    op.drop_table('institution_certificate_requests')

    student_document_status.drop(op.get_bind(), checkfirst=True)
    institution_request_status.drop(op.get_bind(), checkfirst=True)

    # ALTER TYPE ... DROP VALUE has no direct equivalent — left as a no-op,
    # same rationale as the 'other' credential_type migration.
