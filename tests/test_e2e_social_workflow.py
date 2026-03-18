"""
End-to-end test for complete social media workflow.

Tests the complete social media workflow from request to publication:
1. Social post request received
2. Action item created (orchestrator)
3. Post drafted (social_mcp/twitter_mcp)
4. Approval requested (approval_executor)
5. Approval granted (approval_executor)
6. Post published to social media (social_mcp/twitter_mcp)

Verifies all steps are logged with correct workflow_id and traceability.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from scripts.audit_logger import AuditLogger
from scripts.audit_search import AuditSearch


class TestE2ESocialWorkflow:
    """End-to-end tests for complete social media workflow."""

    def test_complete_social_post_workflow(self, audit_logger_with_config):
        """
        Test complete social media post workflow with full audit trail.

        Workflow:
        1. Social post request received
        2. Action item created
        3. Post drafted
        4. Approval requested
        5. Approval granted
        6. Post published

        Verify: All actions logged with workflow_id and parent_action_id
        """
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-social-001"

        # Step 1: Social post request received
        step1_id = audit_logger.log_action(
            action_type="social_post_request",
            actor="orchestrator",
            target="social_queue",
            parameters={
                "platform": "twitter",
                "content_type": "announcement",
                "topic": "New product launch"
            },
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Step 2: Action item created
        step2_id = audit_logger.log_action(
            action_type="file_write",
            actor="orchestrator",
            target="Needs_Action/SOCIAL_product_launch.md",
            parameters={
                "content_preview": "Draft social post for product launch"
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step1_id
            }
        )

        # Step 3: Post drafted
        step3_id = audit_logger.log_action(
            action_type="social_post_draft",
            actor="twitter_mcp",
            target="twitter",
            parameters={
                "content": "Excited to announce our new product! 🚀 #ProductLaunch",
                "platform": "twitter",
                "character_count": 58
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step2_id
            }
        )

        # Step 4: Approval requested
        step4_id = audit_logger.log_action(
            action_type="approval_request",
            actor="orchestrator",
            target="Pending_Approval/APPROVAL_social_post.md",
            parameters={
                "action_type": "social_post_publish",
                "risk_assessment": "low",
                "platform": "twitter"
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step3_id
            }
        )

        # Step 5: Approval granted
        step5_id = audit_logger.log_action(
            action_type="approval_granted",
            actor="approval_executor",
            target="approval-social-001",
            parameters={
                "approver": "human_admin",
                "action_type": "social_post_publish"
            },
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "human_admin",
                "approved_at": datetime.utcnow().isoformat() + 'Z'
            },
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step4_id
            }
        )

        # Step 6: Post published
        step6_id = audit_logger.log_action(
            action_type="social_post_publish",
            actor="twitter_mcp",
            target="twitter",
            parameters={
                "content": "Excited to announce our new product! 🚀 #ProductLaunch",
                "platform": "twitter",
                "post_id": "tweet-12345"
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step5_id,
                "post_url": "https://twitter.com/user/status/12345"
            }
        )

        audit_logger.flush()

        # Verify workflow traceability
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        # Verify all 6 steps are logged
        assert len(workflow_entries) == 6

        # Verify workflow order
        assert workflow_entries[0]["action_type"] == "social_post_request"
        assert workflow_entries[1]["action_type"] == "file_write"
        assert workflow_entries[2]["action_type"] == "social_post_draft"
        assert workflow_entries[3]["action_type"] == "approval_request"
        assert workflow_entries[4]["action_type"] == "approval_granted"
        assert workflow_entries[5]["action_type"] == "social_post_publish"

        # Verify parent-child relationships
        assert workflow_entries[1]["metadata"]["parent_action_id"] == step1_id
        assert workflow_entries[2]["metadata"]["parent_action_id"] == step2_id
        assert workflow_entries[3]["metadata"]["parent_action_id"] == step3_id
        assert workflow_entries[4]["metadata"]["parent_action_id"] == step4_id
        assert workflow_entries[5]["metadata"]["parent_action_id"] == step5_id

        # Verify approval information
        assert workflow_entries[4]["approval"]["status"] == "approved"
        assert workflow_entries[4]["approval"]["approver"] == "human_admin"

        # Verify post details preserved
        assert workflow_entries[5]["parameters"]["post_id"] == "tweet-12345"
        assert "post_url" in workflow_entries[5]["metadata"]

    def test_social_workflow_with_rejection(self, audit_logger_with_config):
        """Test social media workflow where approval is denied."""
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-social-rejected-001"

        # Steps 1-4: Same as above (request, create, draft, request approval)
        step1_id = audit_logger.log_action(
            action_type="social_post_request",
            actor="orchestrator",
            target="social_queue",
            parameters={
                "platform": "twitter",
                "content_type": "controversial"
            },
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        step2_id = audit_logger.log_action(
            action_type="social_post_draft",
            actor="twitter_mcp",
            target="twitter",
            parameters={
                "content": "Controversial statement that needs review",
                "platform": "twitter"
            },
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": step1_id}
        )

        step3_id = audit_logger.log_action(
            action_type="approval_request",
            actor="orchestrator",
            target="Pending_Approval/APPROVAL_controversial_post.md",
            parameters={
                "action_type": "social_post_publish",
                "risk_assessment": "high"
            },
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": step2_id}
        )

        # Step 4: Approval denied
        step4_id = audit_logger.log_action(
            action_type="approval_denied",
            actor="approval_executor",
            target="approval-social-002",
            parameters={
                "approver": "human_admin",
                "reason": "Content not aligned with brand guidelines"
            },
            result="success",
            approval={
                "required": True,
                "status": "denied",
                "approver": "human_admin",
                "denied_at": datetime.utcnow().isoformat() + 'Z'
            },
            metadata={"workflow_id": workflow_id, "parent_action_id": step3_id}
        )

        audit_logger.flush()

        # Verify workflow
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        assert len(workflow_entries) == 4
        assert workflow_entries[3]["action_type"] == "approval_denied"
        assert workflow_entries[3]["approval"]["status"] == "denied"

    def test_social_workflow_with_publish_failure(self, audit_logger_with_config):
        """Test social media workflow with publish failure."""
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-social-failed-001"

        # Step 1: Post request received
        step1_id = audit_logger.log_action(
            action_type="social_post_request",
            actor="orchestrator",
            target="social_queue",
            parameters={"platform": "twitter"},
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Step 2: Approval granted
        step2_id = audit_logger.log_action(
            action_type="approval_granted",
            actor="approval_executor",
            target="approval-social-003",
            parameters={"action_type": "social_post_publish"},
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "human_admin",
                "approved_at": datetime.utcnow().isoformat() + 'Z'
            },
            metadata={"workflow_id": workflow_id, "parent_action_id": step1_id}
        )

        # Step 3: Publish fails
        step3_id = audit_logger.log_action(
            action_type="social_post_publish",
            actor="twitter_mcp",
            target="twitter",
            parameters={
                "content": "Test post",
                "platform": "twitter"
            },
            result="failure",
            error="Twitter API rate limit exceeded",
            metadata={"workflow_id": workflow_id, "parent_action_id": step2_id}
        )

        audit_logger.flush()

        # Verify failure is logged
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        assert len(workflow_entries) == 3
        assert workflow_entries[2]["result"] == "failure"
        assert "rate limit" in workflow_entries[2]["error"].lower()

    def test_multi_platform_social_workflow(self, audit_logger_with_config):
        """Test social media workflow posting to multiple platforms."""
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-social-multi-001"

        # Step 1: Multi-platform post request
        step1_id = audit_logger.log_action(
            action_type="social_post_request",
            actor="orchestrator",
            target="social_queue",
            parameters={
                "platforms": ["twitter", "facebook", "instagram"],
                "content_type": "announcement"
            },
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Step 2: Approval granted for all platforms
        step2_id = audit_logger.log_action(
            action_type="approval_granted",
            actor="approval_executor",
            target="approval-social-multi-001",
            parameters={
                "action_type": "social_post_publish",
                "platforms": ["twitter", "facebook", "instagram"]
            },
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "human_admin",
                "approved_at": datetime.utcnow().isoformat() + 'Z'
            },
            metadata={"workflow_id": workflow_id, "parent_action_id": step1_id}
        )

        # Step 3: Publish to Twitter
        step3_id = audit_logger.log_action(
            action_type="social_post_publish",
            actor="twitter_mcp",
            target="twitter",
            parameters={
                "content": "Multi-platform announcement",
                "platform": "twitter",
                "post_id": "tweet-99999"
            },
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": step2_id}
        )

        # Step 4: Publish to Facebook
        step4_id = audit_logger.log_action(
            action_type="social_post_publish",
            actor="social_mcp",
            target="facebook",
            parameters={
                "content": "Multi-platform announcement",
                "platform": "facebook",
                "post_id": "fb-88888"
            },
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": step2_id}
        )

        # Step 5: Publish to Instagram
        step5_id = audit_logger.log_action(
            action_type="social_post_publish",
            actor="social_mcp",
            target="instagram",
            parameters={
                "content": "Multi-platform announcement",
                "platform": "instagram",
                "post_id": "ig-77777"
            },
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": step2_id}
        )

        audit_logger.flush()

        # Verify workflow
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        # Verify all 5 steps are logged
        assert len(workflow_entries) == 5

        # Verify all three platforms were posted to
        publish_entries = [e for e in workflow_entries if e["action_type"] == "social_post_publish"]
        assert len(publish_entries) == 3

        platforms = [e["parameters"]["platform"] for e in publish_entries]
        assert "twitter" in platforms
        assert "facebook" in platforms
        assert "instagram" in platforms


@pytest.fixture
def audit_logger_with_config(tmp_path):
    """Fixture that creates an AuditLogger with configuration."""
    import os

    config_path = tmp_path / "logging_config.json"
    log_dir = tmp_path / "logs"
    config = {
        "log_directory": str(log_dir),
        "encryption_enabled": False,
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))
    yield logger, log_dir, config_path
    logger.flush()
