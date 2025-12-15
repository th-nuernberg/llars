"""
Markdown Collab Seeder

Creates a demo workspace and a small starter tree in development setups.
Idempotent: will not create duplicates on repeated startups.
"""

from datetime import datetime


def initialize_markdown_collab_defaults(db):
    # Lazy import to avoid circular dependencies
    from ..tables import MarkdownWorkspace, MarkdownDocument, MarkdownNodeType, MarkdownWorkspaceVisibility

    existing = MarkdownWorkspace.query.first()
    if existing:
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
    print(f"✅ Created Markdown Collab demo workspace (id={workspace.id})")
