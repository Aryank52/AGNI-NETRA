import os
import json
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES


VALID_DATASET_TYPES = [
    "REAL",
    "SYNTHETIC",
    "DEMO",
    "WEAKLY_LABELED",
    "HUMAN_VERIFIED"
]


class DatasetBuilder:
    """
    AGNI-NETRA Dataset V2 Builder.
    Manages dataset construction with rigorous provenance tracking.
    Guarantees strict isolation between synthetic calibration data and real-world telemetry.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.dirname(os.path.abspath(__file__))

    def build_real_dataset_sample(
        self,
        event_id: str,
        features: Dict[str, float],
        label: str,
        dataset_type: str = "REAL",
        label_source: str = "NASA_FIRMS_GROUND_TRUTH",
        verification_status: str = "UNVERIFIED",
        state: str = "Gujarat",
        acquisition_date: str = "2026-03-15"
    ) -> Dict[str, Any]:
        """
        Constructs a single standardized dataset sample with full provenance.
        """
        if dataset_type not in VALID_DATASET_TYPES:
            raise ValueError(f"Invalid dataset_type '{dataset_type}'. Must be one of {VALID_DATASET_TYPES}")

        if label not in CLASS_NAMES:
            raise ValueError(f"Invalid class label '{label}'. Must be in {CLASS_NAMES}")

        sample = {
            "sample_id": str(uuid.uuid4()),
            "event_id": event_id,
            "dataset_type": dataset_type,
            "label_source": label_source,
            "verification_status": verification_status,
            "state": state,
            "acquisition_date": acquisition_date,
            "label": label,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Attach all 18 feature dimensions
        for col in FEATURE_COLUMNS:
            sample[col] = float(features.get(col, 0.0))

        return sample

    def filter_dataset(
        self,
        samples: List[Dict[str, Any]],
        permitted_types: List[str] = ["REAL", "HUMAN_VERIFIED"]
    ) -> pd.DataFrame:
        """
        Filters a collection of samples by permitted dataset types.
        Prevents silent data contamination.
        """
        for pt in permitted_types:
            if pt not in VALID_DATASET_TYPES:
                raise ValueError(f"Unknown permitted type: {pt}")

        filtered = [s for s in samples if s.get("dataset_type") in permitted_types]
        if not filtered:
            return pd.DataFrame(columns=FEATURE_COLUMNS + ["label", "dataset_type", "state", "acquisition_date"])

        df = pd.DataFrame(filtered)
        return df

    def save_dataset_artifact(
        self,
        df: pd.DataFrame,
        dataset_version: str,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Persists dataset to parquet/csv along with metadata manifest.
        """
        out_dir = output_dir or self.data_dir
        os.makedirs(out_dir, exist_ok=True)
        
        file_path = os.path.join(out_dir, f"dataset_{dataset_version}.csv")
        manifest_path = os.path.join(out_dir, f"manifest_{dataset_version}.json")

        df.to_csv(file_path, index=False)

        manifest = {
            "dataset_version": dataset_version,
            "total_samples": len(df),
            "dataset_types": df["dataset_type"].value_counts().to_dict() if "dataset_type" in df else {},
            "class_distribution": df["label"].value_counts().to_dict() if "label" in df else {},
            "state_distribution": df["state"].value_counts().to_dict() if "state" in df else {},
            "feature_columns": FEATURE_COLUMNS,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return file_path


dataset_builder = DatasetBuilder()
