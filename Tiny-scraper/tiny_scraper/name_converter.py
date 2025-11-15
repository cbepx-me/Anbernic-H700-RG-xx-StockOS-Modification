import csv
import re
from pathlib import Path
from difflib import SequenceMatcher


class NameConverter:
    def __init__(self):
        self.mapping_cache = {}
        self.common_patterns = [
            r'^\d+\s*[-.]?\s*',
            r'\s*[-.]?\s*\d+$',
            r'\([^)]*\)',
            r'\[[^\]]*\]',
            r'【[^】]*】',
            r'（[^）]*）',
            r'[vV]\d+\.?\d*',
            r'[vV][eE][rR]\.?\d*',
            r'[fF]inal',
            r'[pP]lus',
            r'[dD][eE][mM][oO]',
            r'[pP][rR][oO][tT][oO]',
            r'[bB][eE][tT][aA]',
            r'[aA][lL][pP][hH][aA]',
            r'[cC][hH][iI][nN][eE][sS][eE]',
            r'[jJ][aA][pP][aA][nN]',
            r'[uU][sS][aA]',
            r'[eE][uU][rR]',
            r'[hH][aA][cC][kK]',
            r'[tT][rR][aA][iI][nN][eE][rR]',
            r'[cC][rR][aA][cC][kK][eE][dD]',
            r'[pP][aA][tT][cC][hH]',
            r'[\u4e00-\u9fff]*版$',
            r'[\u4e00-\u9fff]*汉化$',
        ]

        self.irrelevant_words = {
            'final', 'plus', 'demo', 'beta', 'alpha',
            'chinese', 'japanese', 'english', 'usa', 'europe', 'japan', 'eu',
            'hack', 'trainer', 'cracked', 'patch', 'version', 'ver', 'v',
            '汉化', '中文版', '日版', '美版', '欧版', '最终版', '加强版', '破解版'
        }

    def load_mapping(self, system_name: str) -> dict:
        if system_name in self.mapping_cache:
            return self.mapping_cache[system_name]

        csv_files = [
            f"{system_name}.csv",
            f"Nintendo - {system_name}.csv",
            f"Sony - {system_name}.csv",
            f"Sega - {system_name}.csv",
        ]

        mapping = {}
        script_dir = Path(__file__).parent
        csv_dir = script_dir / "csv"

        if not csv_dir.exists():
            csv_dir = script_dir

        for csv_file in csv_files:
            csv_path = csv_dir / csv_file
            if csv_path.exists():
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader)
                        for row in reader:
                            if len(row) >= 2:
                                en_name = self.normalize_name(row[0].strip())
                                cn_name = self.normalize_name(row[1].strip())
                                mapping[cn_name] = en_name
                                mapping[en_name] = cn_name
                    print(f"Loaded mapping for {system_name} from {csv_file}, total {len(mapping) // 2} entries")
                    break
                except Exception as e:
                    print(f"Error loading CSV {csv_file}: {e}")

        self.mapping_cache[system_name] = mapping
        return mapping

    def is_chinese_name(self, name: str) -> bool:
        for char in name:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False

    def normalize_name(self, name: str) -> str:
        name = name.lower()

        for pattern in self.common_patterns:
            name = re.sub(pattern, '', name)

        name = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    def extract_core_name(self, filename: str) -> str:
        name = Path(filename).stem

        normalized = self.normalize_name(name)

        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', normalized)

        filtered_words = []
        for word in words:
            if (word not in self.irrelevant_words and
                    not word.isdigit() and
                    len(word) > 1):
                filtered_words.append(word)

        core_name = ' '.join(filtered_words)

        return core_name.strip()

    def similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def find_best_match(self, target: str, candidates: list, threshold: float = 0.6) -> str:
        best_match = None
        best_score = 0

        for candidate in candidates:
            score = self.similarity(target, candidate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate

        return best_match if best_match else target

    def convert_to_english(self, system_name: str, chinese_name: str) -> str:
        mapping = self.load_mapping(system_name)

        core_name = self.extract_core_name(chinese_name)

        print(f"Original: '{chinese_name}' -> Core: '{core_name}'")

        if core_name in mapping:
            result = mapping[core_name]
            print(f"Exact match found: {result}")
            return result

        chinese_keys = [k for k in mapping.keys() if self.is_chinese_name(k)]
        best_chinese_match = self.find_best_match(core_name, chinese_keys)

        if best_chinese_match != core_name:
            result = mapping[best_chinese_match]
            print(f"Fuzzy match found: '{best_chinese_match}' -> {result}")
            return result

        chinese_only = ''.join(re.findall(r'[\u4e00-\u9fff]+', core_name))
        if chinese_only and chinese_only != core_name:
            best_chinese_only_match = self.find_best_match(chinese_only, chinese_keys, 0.4)
            if best_chinese_only_match != chinese_only:
                result = mapping[best_chinese_only_match]
                print(f"Chinese-only match found: '{best_chinese_only_match}' -> {result}")
                return result

        series_matches = self.series_match(core_name, chinese_keys)
        if series_matches:
            best_series_match = self.find_best_match(core_name, series_matches, 0.3)
            if best_series_match:
                result = mapping[best_series_match]
                print(f"Series match found: '{best_series_match}' -> {result}")
                return result

        print(f"No English mapping found for '{chinese_name}' in {system_name}")
        return chinese_name

    def series_match(self, target: str, candidates: list) -> list:
        series_keywords = [
            '勇者斗恶龙', '最终幻想', '口袋妖怪', '塞尔达', '马里奥',
            '星之卡比', '火焰纹章', '恶魔城', '洛克人', '合金装备',
            'dragon quest', 'final fantasy', 'pokemon', 'zelda', 'mario',
            'kirby', 'fire emblem', 'castlevania', 'mega man', 'metal gear'
        ]

        matching_series = []
        for keyword in series_keywords:
            if keyword in target.lower():
                for candidate in candidates:
                    if keyword in candidate.lower():
                        matching_series.append(candidate)
                break

        return matching_series

    def clean_filename(self, filename: str) -> str:
        return self.extract_core_name(filename)


name_converter = NameConverter()