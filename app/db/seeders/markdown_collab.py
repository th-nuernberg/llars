"""
Markdown Collab Seeder

Creates a demo workspace and a small starter tree in development setups.
Idempotent: will not create duplicates on repeated startups.
"""

from datetime import datetime


def _ensure_markdown_commits(db, workspace, message):
    from ..tables import MarkdownCommit, MarkdownDocument, MarkdownNodeType

    docs = (
        MarkdownDocument.query
        .filter_by(workspace_id=workspace.id)
        .filter(MarkdownDocument.node_type == MarkdownNodeType.file)
        .filter(MarkdownDocument.deleted_at.is_(None))
        .all()
    )
    if not docs:
        return 0

    created_at = datetime.utcnow()
    created = 0

    for doc in docs:
        if MarkdownCommit.query.filter_by(document_id=doc.id).first():
            continue
        content_snapshot = doc.content_text or ""
        commit = MarkdownCommit(
            document_id=doc.id,
            author_username='admin',
            message=message,
            diff_summary={"files_added": 1},
            content_snapshot=content_snapshot,
            created_at=created_at,
        )
        db.session.add(commit)
        created += 1

    if created:
        db.session.commit()
    return created


def initialize_markdown_collab_defaults(db):
    # Lazy import to avoid circular dependencies
    from ..tables import MarkdownWorkspace, MarkdownDocument, MarkdownNodeType, MarkdownWorkspaceVisibility

    existing = MarkdownWorkspace.query.filter_by(name='Markdown Collab Demo').first()
    if existing:
        created = _ensure_markdown_commits(db, existing, "Initial commit: Markdown Collab Demo")
        if created:
            print(f"✅ Backfilled {created} markdown commits for demo workspace (id={existing.id})")
        return

    workspace = MarkdownWorkspace(
        name='Markdown Collab Demo',
        owner_username='admin',
        visibility=MarkdownWorkspaceVisibility.private,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(workspace)
    db.session.flush()

    research = MarkdownDocument(
        workspace_id=workspace.id,
        parent_id=None,
        node_type=MarkdownNodeType.folder,
        title='Research',
        order_index=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    archive = MarkdownDocument(
        workspace_id=workspace.id,
        parent_id=None,
        node_type=MarkdownNodeType.folder,
        title='Archive',
        order_index=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(research)
    db.session.add(archive)
    db.session.flush()

    intro = MarkdownDocument(
        workspace_id=workspace.id,
        parent_id=research.id,
        node_type=MarkdownNodeType.file,
        title='intro.md',
        order_index=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    notes = MarkdownDocument(
        workspace_id=workspace.id,
        parent_id=research.id,
        node_type=MarkdownNodeType.file,
        title='notes.md',
        order_index=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(intro)
    db.session.add(notes)
    db.session.flush()

    # Set yjs room ids for files (folders stay NULL)
    intro.yjs_doc_id = f"markdown_{intro.id}"
    notes.yjs_doc_id = f"markdown_{notes.id}"

    db.session.commit()
    created = _ensure_markdown_commits(db, workspace, "Initial commit: Markdown Collab Demo")
    print(f"✅ Created Markdown Collab demo workspace (id={workspace.id}) with {created} initial commits")
