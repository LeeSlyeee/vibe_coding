"""전국 기초 정신건강복지센터 시드 데이터 등록 스크립트"""
import os, sys, django
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
sys.path.insert(0, "/home/ubuntu/backend_new")
django.setup()

from centers.models import Region, Center

# 기존 센터 코드 목록
existing = set(Center.objects.values_list("code", flat=True))

centers_data = {
    # ===== 서울 (25개) =====
    "SEOUL": [
        ("SEOUL_GANGNAM", "강남구정신건강복지센터"),
        ("SEOUL_GANGDONG", "강동구정신건강복지센터"),
        ("SEOUL_GANGBUK", "강북구정신건강복지센터"),
        ("SEOUL_GANGSEO", "강서구정신건강복지센터"),
        ("SEOUL_GWANAK", "관악구정신건강복지센터"),
        ("SEOUL_GWANGJIN", "광진구정신건강복지센터"),
        ("SEOUL_GURO", "구로구정신건강복지센터"),
        ("SEOUL_GEUMCHEON", "금천구정신건강복지센터"),
        ("SEOUL_NOWON", "노원구정신건강복지센터"),
        ("SEOUL_DOBONG", "도봉구정신건강복지센터"),
        ("SEOUL_DONGDAEMUN", "동대문구정신건강복지센터"),
        ("SEOUL_DONGJAK", "동작구정신건강복지센터"),
        ("SEOUL_MAPO", "마포구정신건강복지센터"),
        ("SEOUL_SEODAEMUN", "서대문구정신건강복지센터"),
        ("SEOUL_SEOCHO", "서초구정신건강복지센터"),
        ("SEOUL_SEONGDONG", "성동구정신건강복지센터"),
        ("SEOUL_SEONGBUK", "성북구정신건강복지센터"),
        ("SEOUL_SONGPA", "송파구정신건강복지센터"),
        ("SEOUL_YANGCHEON", "양천구정신건강복지센터"),
        ("SEOUL_YEONGDEUNGPO", "영등포구정신건강복지센터"),
        ("SEOUL_YONGSAN", "용산구정신건강복지센터"),
        ("SEOUL_EUNPYEONG", "은평구정신건강복지센터"),
        ("SEOUL_JONGNO", "종로구정신건강복지센터"),
        ("SEOUL_JUNGGU", "중구정신건강복지센터"),
        ("SEOUL_JUNGNANG", "중랑구정신건강복지센터"),
    ],
    # ===== 부산 (16개) =====
    "BUSAN": [
        ("BUSAN_GANGSEO", "강서구정신건강복지센터"),
        ("BUSAN_GEUMJEONG", "금정구정신건강복지센터"),
        ("BUSAN_GIJANG", "기장군정신건강복지센터"),
        ("BUSAN_NAMGU", "남구정신건강복지센터"),
        ("BUSAN_DONGGU", "동구정신건강복지센터"),
        ("BUSAN_DONGNAE", "동래구정신건강복지센터"),
        ("BUSAN_BUSANJIN", "부산진구정신건강복지센터"),
        ("BUSAN_BUKGU", "북구정신건강복지센터"),
        ("BUSAN_SASANG", "사상구정신건강복지센터"),
        ("BUSAN_SAHA", "사하구정신건강복지센터"),
        ("BUSAN_SEOGU", "서구정신건강복지센터"),
        ("BUSAN_SUYEONG", "수영구정신건강복지센터"),
        ("BUSAN_YEONJE", "연제구정신건강복지센터"),
        ("BUSAN_YEONGDO", "영도구정신건강복지센터"),
        ("BUSAN_JUNGGU", "중구정신건강복지센터"),
        ("BUSAN_HAEUNDAE", "해운대구정신건강복지센터"),
    ],
    # ===== 대구 (8개) =====
    "DAEGU": [
        ("DAEGU_NAMGU", "남구정신건강복지센터"),
        ("DAEGU_DALSEO", "달서구정신건강복지센터"),
        ("DAEGU_DALSEONG", "달성군정신건강복지센터"),
        ("DAEGU_DONGGU", "동구정신건강복지센터"),
        ("DAEGU_BUKGU", "북구정신건강복지센터"),
        ("DAEGU_SEOGU", "서구정신건강복지센터"),
        ("DAEGU_SUSEONG", "수성구정신건강복지센터"),
        ("DAEGU_JUNGGU", "중구정신건강복지센터"),
    ],
    # ===== 인천 (11개) =====
    "INCHEON": [
        ("INCHEON_GANGHWA", "강화군정신건강복지센터"),
        ("INCHEON_GYEYANG", "계양구정신건강복지센터"),
        ("INCHEON_NAMDONG", "남동구정신건강복지센터"),
        ("INCHEON_DONGGU", "동구정신건강복지센터"),
        ("INCHEON_MICHUHOL", "미추홀구정신건강복지센터"),
        ("INCHEON_BUPYEONG", "부평구정신건강복지센터"),
        ("INCHEON_SEOGU", "서구정신건강복지센터"),
        ("INCHEON_YEONSU", "연수구정신건강복지센터"),
        ("INCHEON_ONGJIN", "옹진군정신건강복지센터"),
        ("INCHEON_JUNGGU", "중구정신건강복지센터"),
        ("INCHEON_YEONGJONG", "영종정신건강복지센터"),
    ],
    # ===== 광주 (5개) =====
    "GWANGJU": [
        ("GWANGJU_GWANGSAN", "광산구정신건강복지센터"),
        ("GWANGJU_NAMGU", "남구정신건강복지센터"),
        ("GWANGJU_DONGGU", "동구정신건강복지센터"),
        ("GWANGJU_BUKGU", "북구정신건강복지센터"),
        ("GWANGJU_SEOGU", "서구정신건강복지센터"),
    ],
    # ===== 대전 (5개) =====
    "DAEJEON": [
        ("DAEJEON_DAEDEOK", "대덕구정신건강복지센터"),
        ("DAEJEON_DONGGU", "동구정신건강복지센터"),
        ("DAEJEON_SEOGU", "서구정신건강복지센터"),
        ("DAEJEON_YUSEONG", "유성구정신건강복지센터"),
        ("DAEJEON_JUNGGU", "중구정신건강복지센터"),
    ],
    # ===== 울산 (5개) =====
    "ULSAN": [
        ("ULSAN_NAMGU", "남구정신건강복지센터"),
        ("ULSAN_DONGGU", "동구정신건강복지센터"),
        ("ULSAN_BUKGU", "북구정신건강복지센터"),
        ("ULSAN_ULJU", "울주군정신건강복지센터"),
        ("ULSAN_JUNGGU", "중구정신건강복지센터"),
    ],
    # ===== 세종 (1개) =====
    "SEJONG": [
        ("SEJONG_MAIN", "세종시정신건강복지센터"),
    ],
    # ===== 경기 (37개) =====
    "GYEONGGI": [
        ("GG_SUWON", "수원시정신건강복지센터"),
        ("GG_SEONGNAM", "성남시정신건강복지센터"),
        ("GG_UIJEONGBU", "의정부시정신건강복지센터"),
        ("GG_ANYANG", "안양시정신건강복지센터"),
        ("GG_BUCHEON", "부천시정신건강복지센터"),
        ("GG_GWANGMYEONG", "광명시정신건강복지센터"),
        ("GG_PYEONGTAEK", "평택시정신건강복지센터"),
        ("GG_DONGDUCHEON", "동두천시정신건강복지센터"),
        ("GG_ANSAN", "안산시정신건강복지센터"),
        ("GG_GOYANG", "고양시정신건강복지센터"),
        ("GG_GWACHEON", "과천시정신건강복지센터"),
        ("GG_GURI", "구리시정신건강복지센터"),
        ("GG_NAMYANGJU", "남양주시정신건강복지센터"),
        ("GG_OSAN", "오산시정신건강복지센터"),
        ("GG_SIHEUNG", "시흥시정신건강복지센터"),
        ("GG_GUNPO", "군포시정신건강복지센터"),
        ("GG_UIWANG", "의왕시정신건강복지센터"),
        ("GG_HANAM", "하남시정신건강복지센터"),
        ("GG_YONGIN", "용인시정신건강복지센터"),
        ("GG_PAJU", "파주시정신건강복지센터"),
        ("GG_ICHEON", "이천시정신건강복지센터"),
        ("GG_ANSEONG", "안성시정신건강복지센터"),
        ("GG_GIMPO", "김포시정신건강복지센터"),
        ("GG_HWASEONG", "화성시정신건강복지센터"),
        ("GG_GWANGJU", "광주시정신건강복지센터"),
        ("GG_YANGJU", "양주시정신건강복지센터"),
        ("GG_POCHEON", "포천시정신건강복지센터"),
        ("GG_YEOJU", "여주시정신건강복지센터"),
        ("GG_YANGPYEONG", "양평군정신건강복지센터"),
        ("GG_GAPYEONG", "가평군정신건강복지센터"),
        ("GG_YEONCHEON", "연천군정신건강복지센터"),
        ("GG_SUWON_JANGAN", "수원시장안구정신건강복지센터"),
        ("GG_SUWON_GWONSEON", "수원시권선구정신건강복지센터"),
        ("GG_SUWON_PALDAL", "수원시팔달구정신건강복지센터"),
        ("GG_SUWON_YEONGTONG", "수원시영통구정신건강복지센터"),
        ("GG_GOYANG_ILSAN", "고양시일산정신건강복지센터"),
        ("GG_GOYANG_DEOGYANG", "고양시덕양구정신건강복지센터"),
    ],
    # ===== 강원 (18개) =====
    "GANGWON": [
        ("GW_CHUNCHEON", "춘천시정신건강복지센터"),
        ("GW_WONJU", "원주시정신건강복지센터"),
        ("GW_GANGNEUNG", "강릉시정신건강복지센터"),
        ("GW_DONGHAE", "동해시정신건강복지센터"),
        ("GW_TAEBAEK", "태백시정신건강복지센터"),
        ("GW_SOKCHO", "속초시정신건강복지센터"),
        ("GW_SAMCHEOK", "삼척시정신건강복지센터"),
        ("GW_HONGCHEON", "홍천군정신건강복지센터"),
        ("GW_HOENGSEONG", "횡성군정신건강복지센터"),
        ("GW_YEONGWOL", "영월군정신건강복지센터"),
        ("GW_PYEONGCHANG", "평창군정신건강복지센터"),
        ("GW_JEONGSEON", "정선군정신건강복지센터"),
        ("GW_CHEORWON", "철원군정신건강복지센터"),
        ("GW_HWACHEON", "화천군정신건강복지센터"),
        ("GW_YANGGU", "양구군정신건강복지센터"),
        ("GW_INJE", "인제군정신건강복지센터"),
        ("GW_GOSEONG", "고성군정신건강복지센터"),
        ("GW_YANGYANG", "양양군정신건강복지센터"),
    ],
    # ===== 충북 (14개) =====
    "CHUNGBUK": [
        ("CB_CHEONGJU", "청주시정신건강복지센터"),
        ("CB_CHUNGJU", "충주시정신건강복지센터"),
        ("CB_JECHEON", "제천시정신건강복지센터"),
        ("CB_BOEUN", "보은군정신건강복지센터"),
        ("CB_OKCHEON", "옥천군정신건강복지센터"),
        ("CB_YEONGDONG", "영동군정신건강복지센터"),
        ("CB_JEUNGPYEONG", "증평군정신건강복지센터"),
        ("CB_JINCHEON", "진천군정신건강복지센터"),
        ("CB_GOESAN", "괴산군정신건강복지센터"),
        ("CB_EUMSEONG", "음성군정신건강복지센터"),
        ("CB_DANYANG", "단양군정신건강복지센터"),
        ("CB_CHEONGJU_SANGDANG", "청주시상당구정신건강복지센터"),
        ("CB_CHEONGJU_SEOWON", "청주시서원구정신건강복지센터"),
        ("CB_CHEONGJU_HEUNGDEOK", "청주시흥덕구정신건강복지센터"),
    ],
    # ===== 충남 (16개) =====
    "CHUNGNAM": [
        ("CN_CHEONAN", "천안시정신건강복지센터"),
        ("CN_GONGJU", "공주시정신건강복지센터"),
        ("CN_BORYEONG", "보령시정신건강복지센터"),
        ("CN_ASAN", "아산시정신건강복지센터"),
        ("CN_SEOSAN", "서산시정신건강복지센터"),
        ("CN_NONSAN", "논산시정신건강복지센터"),
        ("CN_GYERYONG", "계룡시정신건강복지센터"),
        ("CN_DANGJIN", "당진시정신건강복지센터"),
        ("CN_GEUMSAN", "금산군정신건강복지센터"),
        ("CN_BUYEO", "부여군정신건강복지센터"),
        ("CN_SEOCHEON", "서천군정신건강복지센터"),
        ("CN_CHEONGYANG", "청양군정신건강복지센터"),
        ("CN_HONGSEONG", "홍성군정신건강복지센터"),
        ("CN_YESAN", "예산군정신건강복지센터"),
        ("CN_TAEAN", "태안군정신건강복지센터"),
        ("CN_CHEONAN_DONGNAM", "천안시동남구정신건강복지센터"),
    ],
    # ===== 전북 (11개) =====
    "JEONBUK": [
        ("JB_JEONJU", "전주시정신건강복지센터"),
        ("JB_GUNSAN", "군산시정신건강복지센터"),
        ("JB_IKSAN", "익산시정신건강복지센터"),
        ("JB_JEONGEUP", "정읍시정신건강복지센터"),
        ("JB_NAMWON", "남원시정신건강복지센터"),
        ("JB_GIMJE", "김제시정신건강복지센터"),
        ("JB_WANJU", "완주군정신건강복지센터"),
        ("JB_JINAN", "진안군정신건강복지센터"),
        ("JB_MUJU", "무주군정신건강복지센터"),
        ("JB_IMSIL", "임실군정신건강복지센터"),
        ("JB_SUNCHANG", "순창군정신건강복지센터"),
    ],
    # ===== 전남 (22개) =====
    "JEONNAM": [
        ("JN_MOKPO", "목포시정신건강복지센터"),
        ("JN_YEOSU", "여수시정신건강복지센터"),
        ("JN_SUNCHEON", "순천시정신건강복지센터"),
        ("JN_NAJU", "나주시정신건강복지센터"),
        ("JN_GWANGYANG", "광양시정신건강복지센터"),
        ("JN_DAMYANG", "담양군정신건강복지센터"),
        ("JN_GOKSEONG", "곡성군정신건강복지센터"),
        ("JN_GURYE", "구례군정신건강복지센터"),
        ("JN_GOHEUNG", "고흥군정신건강복지센터"),
        ("JN_BOSEONG", "보성군정신건강복지센터"),
        ("JN_HWASUN", "화순군정신건강복지센터"),
        ("JN_JANGHEUNG", "장흥군정신건강복지센터"),
        ("JN_GANGJIN", "강진군정신건강복지센터"),
        ("JN_HAENAM", "해남군정신건강복지센터"),
        ("JN_YEONGAM", "영암군정신건강복지센터"),
        ("JN_MUAN", "무안군정신건강복지센터"),
        ("JN_HAMPYEONG", "함평군정신건강복지센터"),
        ("JN_YEONGGWANG", "영광군정신건강복지센터"),
        ("JN_JANGSEONG", "장성군정신건강복지센터"),
        ("JN_WANDO", "완도군정신건강복지센터"),
        ("JN_JINDO", "진도군정신건강복지센터"),
        ("JN_SINAN", "신안군정신건강복지센터"),
    ],
    # ===== 경북 (25개) =====
    "GYEONGBUK": [
        ("GB_POHANG", "포항시정신건강복지센터"),
        ("GB_GYEONGJU", "경주시정신건강복지센터"),
        ("GB_GIMCHEON", "김천시정신건강복지센터"),
        ("GB_ANDONG", "안동시정신건강복지센터"),
        ("GB_GUMI", "구미시정신건강복지센터"),
        ("GB_YEONGJU", "영주시정신건강복지센터"),
        ("GB_YEONGCHEON", "영천시정신건강복지센터"),
        ("GB_SANGJU", "상주시정신건강복지센터"),
        ("GB_MUNGYEONG", "문경시정신건강복지센터"),
        ("GB_GYEONGSAN", "경산시정신건강복지센터"),
        ("GB_GUNWI", "군위군정신건강복지센터"),
        ("GB_UISEONG", "의성군정신건강복지센터"),
        ("GB_CHEONGSONG", "청송군정신건강복지센터"),
        ("GB_YEONGYANG", "영양군정신건강복지센터"),
        ("GB_YEONGDEOK", "영덕군정신건강복지센터"),
        ("GB_CHEONGDO", "청도군정신건강복지센터"),
        ("GB_GORYEONG", "고령군정신건강복지센터"),
        ("GB_SEONGJU", "성주군정신건강복지센터"),
        ("GB_CHILGOK", "칠곡군정신건강복지센터"),
        ("GB_YECHEON", "예천군정신건강복지센터"),
        ("GB_BONGHWA", "봉화군정신건강복지센터"),
        ("GB_ULJIN", "울진군정신건강복지센터"),
        ("GB_ULLEUNG", "울릉군정신건강복지센터"),
        ("GB_POHANG_NAM", "포항시남구정신건강복지센터"),
        ("GB_POHANG_BUK", "포항시북구정신건강복지센터"),
    ],
    # ===== 경남 (20개) =====
    "GYEONGNAM": [
        ("GN_CHANGWON", "창원시정신건강복지센터"),
        ("GN_JINJU", "진주시정신건강복지센터"),
        ("GN_TONGYEONG", "통영시정신건강복지센터"),
        ("GN_SACHEON", "사천시정신건강복지센터"),
        ("GN_GIMHAE", "김해시정신건강복지센터"),
        ("GN_MIRYANG", "밀양시정신건강복지센터"),
        ("GN_GEOJE", "거제시정신건강복지센터"),
        ("GN_YANGSAN", "양산시정신건강복지센터"),
        ("GN_UIRYEONG", "의령군정신건강복지센터"),
        ("GN_HAMAN", "함안군정신건강복지센터"),
        ("GN_CHANGNYEONG", "창녕군정신건강복지센터"),
        ("GN_GOSEONG", "고성군정신건강복지센터"),
        ("GN_NAMHAE", "남해군정신건강복지센터"),
        ("GN_HADONG", "하동군정신건강복지센터"),
        ("GN_SANCHEONG", "산청군정신건강복지센터"),
        ("GN_HAMYANG", "함양군정신건강복지센터"),
        ("GN_GEOCHANG", "거창군정신건강복지센터"),
        ("GN_HAPCHEON", "합천군정신건강복지센터"),
        ("GN_CHANGWON_MASANHAPPO", "창원시마산합포구정신건강복지센터"),
        ("GN_CHANGWON_SEONGSAN", "창원시성산구정신건강복지센터"),
    ],
    # ===== 제주 (2개) =====
    "JEJU": [
        ("JEJU_JEJU", "제주시정신건강복지센터"),
        ("JEJU_SEOGWIPO", "서귀포시정신건강복지센터"),
    ],
}

created_count = 0
skipped_count = 0

for region_code, center_list in centers_data.items():
    try:
        region = Region.objects.get(code=region_code)
    except Region.DoesNotExist:
        print(f"[SKIP] Region {region_code} not found")
        continue

    for code, name in center_list:
        if code in existing:
            skipped_count += 1
            continue
        Center.objects.create(
            code=code,
            name=name,
            region=region,
            is_active=True,
        )
        created_count += 1

total = sum(len(v) for v in centers_data.values())
print(f"=== 시드 데이터 등록 완료 ===")
print(f"전체: {total}개 | 신규 생성: {created_count}개 | 기존 스킵: {skipped_count}개")
print(f"DB 센터 총 수: {Center.objects.count()}")
