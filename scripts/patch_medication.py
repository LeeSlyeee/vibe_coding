#!/usr/bin/env python3
"""
diaries 테이블에 medication, medication_desc 컬럼 추가
Flask models.py에 필드 추가
Flask app.py의 serialize_diary에서 하드코딩 False 제거
Flask app.py의 create_diary에서 medication 데이터 저장 추가
Django models.py에 필드 추가
"""
import subprocess

print("=" * 60)
print("[Step 1] DB 컬럼 추가: diaries.medication, diaries.medication_desc")
print("=" * 60)

# Step 1: ALTER TABLE
alter_sql = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='diaries' AND column_name='medication') THEN
        ALTER TABLE diaries ADD COLUMN medication BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'medication 컬럼 추가됨';
    ELSE
        RAISE NOTICE 'medication 컬럼 이미 존재';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='diaries' AND column_name='medication_desc') THEN
        ALTER TABLE diaries ADD COLUMN medication_desc TEXT;
        RAISE NOTICE 'medication_desc 컬럼 추가됨';
    ELSE
        RAISE NOTICE 'medication_desc 컬럼 이미 존재';
    END IF;
END $$;
"""

import os, sys
sys.path.insert(0, '/home/ubuntu/backend_new')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.db import connection
cursor = connection.cursor()
cursor.execute(alter_sql)
connection.commit()
print("✅ DB 컬럼 추가 완료")

# 검증
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='diaries' AND column_name IN ('medication', 'medication_desc')")
cols = [r[0] for r in cursor.fetchall()]
print(f"   검증: {cols}")

print()
print("=" * 60)
print("[Step 2] Flask models.py 수정: Diary 모델에 medication 필드 추가")
print("=" * 60)

models_path = '/home/ubuntu/project/backend/models.py'
with open(models_path, 'r') as f:
    models_content = f.read()

if 'medication' not in models_content:
    # safety_flag 라인 뒤에 추가
    old = "    safety_flag = db.Column(db.Boolean, nullable=True)"
    new = """    safety_flag = db.Column(db.Boolean, nullable=True)
    
    # [New] 약물 복용 데이터
    medication = db.Column(db.Boolean, default=False, nullable=True)
    medication_desc = db.Column(db.Text, nullable=True)"""
    
    models_content = models_content.replace(old, new)
    with open(models_path, 'w') as f:
        f.write(models_content)
    print("✅ models.py 수정 완료")
else:
    print("⏭️ models.py에 이미 medication 필드 존재")

print()
print("=" * 60)
print("[Step 3] Flask app.py 수정: create_diary에 medication 저장 + serialize에 실제 값 반환")
print("=" * 60)

app_path = '/home/ubuntu/project/backend/app.py'
with open(app_path, 'r') as f:
    app_content = f.read()

# 3-1. create_diary에서 Diary 생성 시 medication 추가
old_create = "        safety_flag=data.get('safety_flag', False)\n    )"
new_create = """        safety_flag=data.get('safety_flag', False),
        medication=data.get('medication', False),
        medication_desc=data.get('medication_desc')
    )"""

if 'medication=data.get' not in app_content:
    app_content = app_content.replace(old_create, new_create)
    print("✅ create_diary에 medication 저장 로직 추가")
else:
    print("⏭️ create_diary에 이미 medication 저장 로직 존재")

# 3-2. serialize_diary에서 하드코딩 False → 실제 값
old_serialize = "'medication': False,"
new_serialize = "'medication': getattr(d, 'medication', False) or False,"

if old_serialize in app_content:
    app_content = app_content.replace(old_serialize, new_serialize)
    print("✅ serialize_diary에서 하드코딩 False → 실제 DB 값으로 변경")
else:
    print("⏭️ serialize_diary 이미 수정됨 또는 패턴 불일치")

# 3-3. serialize에 medication_desc도 추가
if "'medication_desc'" not in app_content:
    old_symptoms = "'symptoms': []"
    new_symptoms = "'medication_desc': getattr(d, 'medication_desc', None) or '',\n        'symptoms': []"
    app_content = app_content.replace(old_symptoms, new_symptoms, 1)
    print("✅ serialize_diary에 medication_desc 필드 추가")

with open(app_path, 'w') as f:
    f.write(app_content)

print()
print("=" * 60)
print("[Step 4] Django models.py 수정: MaumOn 모델에 medication 필드 추가")
print("=" * 60)

django_models_path = '/home/ubuntu/backend_new/maum_on/models.py'
with open(django_models_path, 'r') as f:
    django_content = f.read()

if 'medication' not in django_content:
    # safety_flag 라인 뒤에 추가
    old_django = "    safety_flag = models.BooleanField(null=True, blank=True)"
    new_django = """    safety_flag = models.BooleanField(null=True, blank=True)
    medication = models.BooleanField(null=True, blank=True, default=False)
    medication_desc = models.TextField(null=True, blank=True)"""
    
    if old_django in django_content:
        django_content = django_content.replace(old_django, new_django)
        with open(django_models_path, 'w') as f:
            f.write(django_content)
        print("✅ Django models.py 수정 완료")
    else:
        print("⚠️ Django models.py에서 safety_flag 라인을 찾을 수 없습니다. 수동 확인 필요")
else:
    print("⏭️ Django models.py에 이미 medication 필드 존재")

print()
print("=" * 60)
print("[Step 5] Django staff_patient_views.py 수정: 일기 응답에 medication 포함")
print("=" * 60)

views_path = '/home/ubuntu/backend_new/maum_on/staff_patient_views.py'
with open(views_path, 'r') as f:
    views_content = f.read()

if 'medication' not in views_content:
    # 기존 일기 직렬화 부분에 medication 추가 필요
    # 'safety_flag' 다음에 추가
    old_view = "'safety_flag': d.safety_flag,"
    new_view = """'safety_flag': d.safety_flag,
                    'medication_taken': d.medication if hasattr(d, 'medication') else None,
                    'medication_desc': d.medication_desc if hasattr(d, 'medication_desc') else '',"""
    
    if old_view in views_content:
        views_content = views_content.replace(old_view, new_view)
        with open(views_path, 'w') as f:
            f.write(views_content)
        print("✅ staff_patient_views.py 수정 완료")
    else:
        print("⚠️ 패턴을 찾을 수 없습니다. 수동 확인 필요")
        # 대안: 그냥 위치를 찾아 직접 삽입
        # safety_flag 검색
        import re
        m = re.search(r"'safety_flag':\s*d\.safety_flag", views_content)
        if m:
            print(f"   safety_flag 발견 위치: {m.start()}")
else:
    print("⏭️ staff_patient_views.py에 이미 medication 포함")

print()
print("=" * 60)
print("[최종 검증]")
print("=" * 60)

cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='diaries' AND column_name IN ('medication', 'medication_desc') ORDER BY column_name")
final_cols = [r[0] for r in cursor.fetchall()]
print(f"DB 컬럼 확인: {final_cols}")

# models.py 검증
with open(models_path, 'r') as f:
    flask_check = 'medication' in f.read()
print(f"Flask models.py medication 필드: {'✅' if flask_check else '❌'}")

with open(app_path, 'r') as f:
    app_check_content = f.read()
    app_create_check = 'medication=data.get' in app_check_content
    app_serialize_check = "'medication': getattr" in app_check_content
print(f"Flask app.py create_diary medication: {'✅' if app_create_check else '❌'}")
print(f"Flask app.py serialize medication: {'✅' if app_serialize_check else '❌'}")

print()
print("🎯 모든 수정 완료. Flask와 Django 서비스 재시작이 필요합니다.")
