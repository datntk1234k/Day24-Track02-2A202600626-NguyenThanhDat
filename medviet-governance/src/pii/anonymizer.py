# src/pii/anonymizer.py
import hashlib
import secrets

import pandas as pd
from faker import Faker

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")
Faker.seed(42)

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """Anonymize text theo strategy đã chọn."""
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        replacement_plan: list[tuple[int, int, str]] = []
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            original_value = text[result.start:result.end]
            replacement_plan.append(
                (
                    result.start,
                    result.end,
                    self._replacement_for_entity(
                        entity=result.entity_type,
                        original_value=original_value,
                        strategy=strategy,
                    ),
                )
            )

        anonymized_text = text
        for start, end, replacement in replacement_plan:
            anonymized_text = anonymized_text[:start] + replacement + anonymized_text[end:]

        return anonymized_text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Anonymize toàn bộ DataFrame theo policy của bài lab."""
        df_anon = df.copy()

        for column in ["ho_ten", "dia_chi", "email", "bac_si_phu_trach"]:
            if column in df_anon.columns:
                df_anon[column] = df_anon[column].astype(str).apply(self.anonymize_text)

        if "cccd" in df_anon.columns:
            df_anon["cccd"] = [
                f"FAKE_CCCD_{self._generate_fake_cccd()}" for _ in range(len(df_anon))
            ]

        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [
                f"ANON_PHONE_{self._generate_fake_phone()}" for _ in range(len(df_anon))
            ]

        if "ngay_sinh" in df_anon.columns:
            df_anon["ngay_sinh"] = (
                df_anon["ngay_sinh"].astype(str).apply(self._generalize_birth_date)
            )

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        TODO: Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0

    def _replacement_for_entity(
        self,
        entity: str,
        original_value: str,
        strategy: str,
    ) -> str:
        if strategy == "replace":
            return {
                "PERSON": fake.name(),
                "EMAIL_ADDRESS": fake.email(),
                "VN_CCCD": self._generate_fake_cccd(),
                "VN_PHONE": self._generate_fake_phone(),
            }.get(entity, "[REDACTED]")

        if strategy == "mask":
            return self._mask_value(original_value)

        if strategy == "hash":
            return hashlib.sha256(original_value.encode("utf-8")).hexdigest()

        if strategy == "generalize":
            return self._generalize_birth_date(original_value)

        raise ValueError(f"Unsupported anonymization strategy: {strategy}")

    @staticmethod
    def _generate_fake_cccd() -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(12))

    @staticmethod
    def _generate_fake_phone() -> str:
        prefix = f"0{secrets.choice(['3', '5', '7', '8', '9'])}"
        return prefix + "".join(str(secrets.randbelow(10)) for _ in range(8))

    @staticmethod
    def _mask_value(value: str) -> str:
        if "@" in value:
            local_part, domain = value.split("@", 1)
            masked_local = local_part[:1] + "*" * max(len(local_part) - 1, 0)
            return f"{masked_local}@{domain}"

        if value.isdigit():
            if len(value) <= 4:
                return "*" * len(value)
            return value[:2] + "*" * (len(value) - 4) + value[-2:]

        parts = value.split()
        masked_parts = []
        for part in parts:
            if len(part) <= 1:
                masked_parts.append(part)
            else:
                masked_parts.append(part[0] + "*" * (len(part) - 1))
        return " ".join(masked_parts)

    @staticmethod
    def _generalize_birth_date(value: str) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            return cleaned

        tokens = cleaned.split("/")
        if len(tokens) == 3:
            return tokens[-1]
        return cleaned
