#!/usr/bin/env python3
"""
PatientDeleteView의 delete 메소드를 패치하여
users 테이블을 참조하는 모든 FK 테이블을 먼저 정리하도록 수정
"""

filepath = '/home/ubuntu/backend_new/maum_on/staff_patient_views.py'
with open(filepath, 'r') as f:
    lines = f.readlines()

# 교체 대상 시작점 찾기
start_idx = None
for i, line in enumerate(lines):
    if '# [실행] Cascade' in line:
        start_idx = i
        break

if start_idx is None:
    print("ERROR: 대상 코드를 찾을 수 없습니다")
    exit(1)

# 끝점 찾기: 파일 끝까지 (마지막 return Response 블록 포함)
end_idx = len(lines) - 1

# 뒤에서부터 마지막 non-empty line 찾기
while end_idx > start_idx and lines[end_idx].strip() == '':
    end_idx -= 1

print(f"교체 범위: {start_idx+1}~{end_idx+1} (총 {end_idx - start_idx + 1}줄)")

new_code = '''        # [실행] 모든 참조 테이블 정리 후 환자 삭제
        # PostgreSQL FK 제약 조건: users를 참조하는 6개 테이블을 순서대로 삭제
        from django.db import connection

        diary_deleted = MaumOn.objects.filter(user=patient).count()

        try:
            with connection.cursor() as cursor:
                # 1. share_relationships (sharer_id, viewer_id 양쪽 참조)
                cursor.execute("DELETE FROM share_relationships WHERE sharer_id = %s OR viewer_id = %s", [patient_id, patient_id])
                share_rel_deleted = cursor.rowcount

                # 2. share_codes
                cursor.execute("DELETE FROM share_codes WHERE user_id = %s", [patient_id])
                share_code_deleted = cursor.rowcount

                # 3. chat_logs
                cursor.execute("DELETE FROM chat_logs WHERE user_id = %s", [patient_id])
                chat_deleted = cursor.rowcount

                # 4. bridge_recipients
                cursor.execute("DELETE FROM bridge_recipients WHERE user_id = %s", [patient_id])
                bridge_recip_deleted = cursor.rowcount

                # 5. bridge_shares
                cursor.execute("DELETE FROM bridge_shares WHERE user_id = %s", [patient_id])
                bridge_share_deleted = cursor.rowcount

                # 6. diaries
                cursor.execute("DELETE FROM diaries WHERE user_id = %s", [patient_id])

                # 7. users 테이블 (최종)
                cursor.execute("DELETE FROM users WHERE id = %s", [patient_id])

            total_extra = share_rel_deleted + share_code_deleted + chat_deleted + bridge_recip_deleted + bridge_share_deleted
            print(f'\\U0001F5D1\\uFE0F [PatientDelete] 환자 삭제 완료: {patient_name} (ID: {patient_id})')
            print(f'   삭제 상세: 일기 {diary_deleted}, 공유관계 {share_rel_deleted}, 공유코드 {share_code_deleted}, 채팅 {chat_deleted}, 브릿지수신 {bridge_recip_deleted}, 브릿지공유 {bridge_share_deleted}')

            return Response({
                'success': True,
                'message': f'환자 "{patient_name}" 및 관련 데이터({diary_deleted}건의 일기 포함)가 영구 삭제되었습니다.',
                'deleted': {
                    'patient_id': patient_id,
                    'username': username,
                    'diary_count': diary_deleted,
                    'related_data': total_extra,
                }
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'삭제 중 오류가 발생했습니다: {str(e)}',
                'detail': '데이터베이스 제약 조건 오류입니다. 관리자에게 문의하세요.'
            }, status=500)
'''

# 교체 적용
new_lines = lines[:start_idx] + [new_code]
with open(filepath, 'w') as f:
    f.writelines(new_lines)

# 문법 검증
import py_compile
try:
    py_compile.compile(filepath, doraise=True)
    print("✅ 패치 적용 및 문법 검증 통과")
except py_compile.PyCompileError as e:
    print(f"❌ 문법 오류: {e}")
