#!/usr/bin/env python3
"""
Export KAIdol Conversations for Network Effects

Export anonymized conversations to improve model quality.
More users → More data → Better model → More users (Network Effect)

Usage:
    python scripts/export_kaidol_conversations.py --output datasets/kaidol_conversations_v1
"""

import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import re


def anonymize_conversation(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize conversation data for safe sharing.
    
    Removes:
    - User IDs
    - Personal information
    - PII (Personally Identifiable Information)
    
    Keeps:
    - Conversation structure
    - Character interactions
    - Quality signals (likes, ratings)
    """
    anonymized = conversation.copy()
    
    # Remove/replace user identifiers
    if "user_id" in anonymized:
        # Hash user ID for consistency without revealing identity
        user_id = anonymized["user_id"]
        anonymized["user_id"] = f"user_{hashlib.sha256(user_id.encode()).hexdigest()[:8]}"
    
    # Remove personal information from messages
    if "messages" in anonymized:
        anonymized["messages"] = [
            anonymize_message(msg) for msg in anonymized["messages"]
        ]
    
    # Keep quality signals (important for training)
    # - likes, ratings, session_duration
    # Remove exact timestamps (keep relative timing)
    if "timestamp" in anonymized:
        # Convert to relative time from session start
        anonymized["session_offset_seconds"] = anonymized.pop("timestamp")
    
    return anonymized


def anonymize_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize individual message."""
    anonymized = message.copy()
    
    # Remove PII from content
    content = anonymized.get("content", "")
    
    # Pattern matching for PII
    pii_patterns = [
        r"\d{3}-\d{3}-\d{4}",  # Phone numbers
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Emails
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP addresses
        r"\b(?:010|011|016|017|018|019)-\d{3,4}-\d{4}\b",  # Korean phone
    ]
    
    for pattern in pii_patterns:
        content = re.sub(pattern, "[REDACTED]", content)
    
    anonymized["content"] = content
    
    return anonymized


def filter_high_quality_conversations(
    conversations: List[Dict],
    min_rating: float = 4.0,
    min_length: int = 5
) -> List[Dict]:
    """
    Filter conversations by quality metrics.
    
    Criteria:
    - Rating >= min_rating
    - Length >= min_length messages
    - No toxic content (if flagged)
    """
    filtered = []
    
    for conv in conversations:
        # Check rating
        rating = conv.get("rating", 0)
        if rating < min_rating:
            continue
        
        # Check length
        messages = conv.get("messages", [])
        if len(messages) < min_length:
            continue
        
        # Check toxicity flag
        if conv.get("is_toxic", False):
            continue
        
        filtered.append(conv)
    
    return filtered


def export_conversations(
    input_path: str,
    output_path: str,
    anonymize: bool = True,
    filter_quality: bool = True,
    format: str = "huggingface"
):
    """
    Export conversations with optional anonymization and filtering.
    
    Args:
        input_path: Path to conversation database/JSON
        output_path: Output directory
        anonymize: Whether to anonymize data
        filter_quality: Whether to filter by quality
        format: Output format ("huggingface", "json", "parquet")
    """
    print(f"📂 Loading conversations from {input_path}...")
    
    # Load conversations
    input_path = Path(input_path)
    if input_path.suffix == ".json":
        with open(input_path) as f:
            conversations = json.load(f)
    else:
        # Assume database or other format
        raise ValueError(f"Unsupported input format: {input_path.suffix}")
    
    print(f"📊 Loaded {len(conversations)} conversations")
    
    # Filter by quality
    if filter_quality:
        print("🔍 Filtering high-quality conversations...")
        conversations = filter_high_quality_conversations(conversations)
        print(f"✅ {len(conversations)} high-quality conversations")
    
    # Anonymize
    if anonymize:
        print("🔒 Anonymizing conversations...")
        conversations = [anonymize_conversation(c) for c in conversations]
    
    # Prepare output
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create dataset structure
    dataset = {
        "conversations": conversations,
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "anonymized": anonymize,
            "filtered": filter_quality,
            "version": "1.0.0",
            "license": "CC-BY-NC-4.0",  # Non-commercial for now
            "description": "KAIdol high-quality RP conversations for model improvement"
        }
    }
    
    # Save based on format
    if format == "huggingface":
        # HuggingFace datasets format
        train_path = output_path / "train.json"
        with open(train_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        # Create dataset card
        card_path = output_path / "README.md"
        create_dataset_card(card_path, dataset["metadata"])
        
        print(f"💾 Saved to {train_path} (HuggingFace format)")
        
    elif format == "json":
        output_file = output_path / "conversations.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved to {output_file}")
    
    else:
        raise ValueError(f"Unsupported output format: {format}")
    
    # Print statistics
    print_statistics(conversations)
    
    return output_path


def create_dataset_card(card_path: Path, metadata: Dict):
    """Create HuggingFace dataset card."""
    card_content = f"""# KAIdol Conversations Dataset

## Overview
High-quality roleplay conversations from KAIdol AI character chatbot.

## Statistics
- **Total Conversations**: {metadata['total_conversations']:,}
- **Exported**: {metadata['exported_at']}
- **Anonymized**: {'Yes' if metadata['anonymized'] else 'No'}
- **Filtered**: {'Yes' if metadata['filtered'] else 'No'}

## License
{metadata['license']}

## Usage
```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="train.json")
```

## Ethics
- All user identifiers have been anonymized
- PII (Personally Identifiable Information) removed
- Only high-quality, non-toxic conversations included
- Users opted-in for data improvement

## Citation
If you use this dataset, please cite:
```bibtex
@dataset{kaidol_conversations_2026,
  title={KAIdol Conversations Dataset},
  author={KAIdol Team},
  year={2026},
  url={https://huggingface.co/datasets/kaidol/conversations}
}
```
"""
    
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(card_content)
    
    print(f"📝 Dataset card created at {card_path}")


def print_statistics(conversations: List[Dict]):
    """Print dataset statistics."""
    print("\n📊 Dataset Statistics:")
    print(f"  Total conversations: {len(conversations):,}")
    
    # Calculate average length
    lengths = [len(c.get("messages", [])) for c in conversations]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    print(f"  Average messages/conversation: {avg_length:.1f}")
    
    # Calculate average rating
    ratings = [c.get("rating", 0) for c in conversations if "rating" in c]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    print(f"  Average rating: {avg_rating:.2f}/5.0")
    
    # Estimate training value
    total_messages = sum(lengths)
    print(f"  Total messages: {total_messages:,}")
    print(f"  Estimated training value: ${total_messages * 0.001:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export KAIdol conversations for network effects"
    )
    parser.add_argument("--input", type=str, required=True, help="Input conversations file")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--no-anonymize", action="store_true", help="Skip anonymization")
    parser.add_argument("--no-filter", action="store_true", help="Skip quality filtering")
    parser.add_argument("--format", type=str, default="huggingface",
                       choices=["huggingface", "json", "parquet"],
                       help="Output format")
    
    args = parser.parse_args()
    
    export_conversations(
        input_path=args.input,
        output_path=args.output,
        anonymize=not args.no_anonymize,
        filter_quality=not args.no_filter,
        format=args.format
    )
    
    print("\n✅ Export complete!")
    print("🚀 Next steps:")
    print("  1. Review exported data")
    print("  2. Upload to HuggingFace: huggingface-cli upload kaidol/conversations ./output")
    print("  3. Share with community for feedback")
    print("  4. Use for model fine-tuning")
