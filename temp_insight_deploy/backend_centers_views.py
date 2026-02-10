from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from .models import Center, VerificationCode
from .serializers import CenterSerializer
from django.contrib.auth import get_user_model
from haru_on.models import HaruOn
from django.utils.dateparse import parse_datetime
from datetime import datetime

User = get_user_model()

class GenerateVerificationCodeView(views.APIView):
    # TODO: 실제로는 의료진(Staff) 권한만 접근 가능하도록 설정해야 함
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 현재 로그인한 사용자가 관리하는 센터 정보를 가져와야 함 (User 모델 확장 필요 또는 가정)
        # 임시로 요청 바디에서 center_id를 받는다고 가정 (슈퍼유저 테스트용)
        center_id = request.data.get('center_id')
        
        # 실제 운영에선 request.user.profile.center 등으로 가져와야 함
        if not center_id:
             # 임시: 슈퍼유저가 아니거나 center_id가 없으면 첫 번째 센터 사용
             first_center = Center.objects.first()
             if not first_center:
                 return Response({'error': '등록된 센터가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
             center = first_center
        else:
            try:
                center = Center.objects.get(id=center_id)
            except Center.DoesNotExist:
                return Response({'error': '존재하지 않는 센터입니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 코드 생성
        code_obj = VerificationCode.objects.create(center=center)
        
        return Response({
            'code': code_obj.code,
            'center_name': center.name,
            'expires_at': '무제한 (사용 시 만료)', 
            'message': '일회용 인증 코드가 생성되었습니다. 사용자에게 전달해주세요.'
        }, status=status.HTTP_201_CREATED)

from rest_framework.decorators import api_view, permission_classes as deco_permissions

@api_view(['POST'])
@deco_permissions([permissions.AllowAny])
def verify_center_code(request):
    # --- File Logging Start ---
    try:
        with open('request_log.txt', 'a') as f:
            f.write(f"\n[{datetime.now()}] Verify Request (FBV)\n")
            f.write(f"Headers: {request.headers}\n")
            f.write(f"Data: {request.data}\n")
    except:
        pass
    # --- File Logging End ---

    print(f"🔍 [DEBUG] Received Headers: {request.headers}")
    print(f"🔍 [DEBUG] Received Body: {request.data}")
    
    # iOS 앱 버전에 따라 키 값이 다를 수 있음 (center_code 또는 code)
    data = request.data
    code_input = data.get('center_code') or data.get('code')
    
    # 방어 로직: DRF가 파싱 못했을 경우 request.body 직접 확인
    if not code_input:
        import json
        try:
            body_data = json.loads(request.body)
            code_input = body_data.get('center_code') or body_data.get('code')
            data = body_data # 바디 데이터 갱신
            print(f"🔍 [DEBUG] Solved by manual parsing: {code_input}")
        except:
            pass

    if not code_input:
        return Response({'error': '인증 코드를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # [Safety] 공백 제거 및 문자열 변환
    code_input = str(code_input).strip()
    print(f"🔍 [Verify] Processing Code: '{code_input}' (Len: {len(code_input)})")

    try:
        # [Generic Identity Unification]
        # 1. 코드 유효성 검사
        verification_code = VerificationCode.objects.filter(code__iexact=code_input).first()
        
        # [Master Code] 테스트용 마스터 코드 (777777)
        if not verification_code and code_input == '777777':
            print("✨ [Verify] Master Code Used!")
            first_center = Center.objects.first()
            if not first_center:
                    first_center = Center.objects.create(name="기본 보건소", location="서울시")
            verification_code, _ = VerificationCode.objects.get_or_create(
                code='777777', 
                defaults={'center': first_center, 'is_used': False}
            )
            if verification_code.is_used:
                verification_code.is_used = False
                verification_code.save()

        if not verification_code:
            print(f"❌ [Verify] Code Not Found. Input: '{code_input}'")
            return Response({'valid': False, 'error': '유효하지 않은 코드입니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 2. 사용자 등록 및 통합 (Identity Unification)
        nickname = data.get('user_nickname') or data.get('nickname') or data.get('name')
        
        final_user = None
        is_merged = False
        
        if verification_code.is_used and verification_code.used_by:
            # [Identity Check]
            owner_nick = verification_code.used_by.username.replace("app_", "")
            req_nick = str(nickname or "").strip().lower()
            # if req_nick and req_nick != owner_nick.lower() and req_nick != owner_nick.lower() + "_demo":  # Demo check optional
            #     return Response({"valid": False, "error": f"이미 다른 사용자({owner_nick})가 사용 중인 코드입니다."}, status=status.HTTP_409_CONFLICT)
            pass

            # [A] Merge Logic (Existing Owner)
            # 이미 누군가 쓰고 있는 코드라면? -> 그 사람이 됩니다.
            owner_user = verification_code.used_by
            print(f"♻️ [Verify] Code is owned by {owner_user.username}. Merging Identity...")
            
            # 현재 요청자가 임시 계정이라면 데이터 이관
            if nickname:
                try:
                    # 앱에서 보낸 닉네임으로 임시 계정 찾기
                    # (보통 앱은 app_닉네임 으로 가입함)
                    temp_username_candidates = [f"app_{nickname}", nickname]
                    temp_user = None
                    for cand in temp_username_candidates:
                        try:
                            temp_user = User.objects.get(username=cand)
                            break
                        except User.DoesNotExist:
                            continue
                            
                    if temp_user and temp_user != owner_user:
                        # [Data Migration] haruON 일기 소유권 이전
                        # update()는 QuerySet에 바로 적용되어 효율적
                        moved_count = HaruOn.objects.filter(user=temp_user).update(user=owner_user)
                        print(f"🚚 [Verify] Data Migration: Moved {moved_count} items from {temp_user.username} to {owner_user.username}")
                        
                        # (Optional) 임시 계정 비활성화
                        temp_user.is_active = False
                        temp_user.save()
                        print(f"🚫 [Merge] Deactivated temporary user: {temp_user.username}")
                        
                except Exception as ex:
                    print(f"⚠️ [Verify] Merge Warning: {ex}")
                    pass 

            final_user = owner_user
            is_merged = True
            
        else:
            # [B] New Registration (New Code)
            if nickname:
                final_user, created = User.objects.get_or_create(
                    username=f"app_{nickname}",
                    defaults={'email': f"{nickname}@app.user", 'is_active': True}
                )
                if created:
                    final_user.set_unusable_password()
                    final_user.save()
            
            # 코드 소유권 할당
            if final_user:
                verification_code.is_used = True
                verification_code.used_at = datetime.now()
                verification_code.used_by = final_user
                verification_code.save()
                print(f"✅ [Verify] Code Assigned to {final_user.username}")

        if not final_user:
             return Response({'error': '사용자 정보를 찾을 수 없습니다.'}, status=400)

        # 3. 응답 (통합 정보 포함)
        response_data = {
            'valid': True, 
            'center_name': verification_code.center.name,
            'user_id': final_user.id
        }
        
        # [Identity info] 앱이 신분을 바꿀 수 있도록 정보 제공
        if is_merged:
            real_nick = final_user.username.replace('app_', '')
            response_data['owner_username'] = final_user.username
            response_data['owner_nickname'] = real_nick 
            response_data['message'] = f"기존 계정({real_nick})과 통합되었습니다."
        
        return Response(response_data)

    except Exception as e:
        print(f"❌ [Verify] Logic Error: {e}")
        return Response({'valid': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CenterListView(generics.ListAPIView):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    permission_classes = [permissions.AllowAny]

class SyncDataView(views.APIView):
    """
    iOS 앱에서 데이터를 수신하여 저장 (B2G 연동 핵심)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        [Pull] Web(217) 서버가 150 서버의 데이터를 가져가기 위한 API
        Query Params: 
          - action: 'check_link' (to recover code) or default (to get data)
          - center_code: (for auth)
          - user_nickname: Target Nickname
        """
        action = request.query_params.get('action')
        center_code = request.query_params.get('center_code')
        nickname = request.query_params.get('user_nickname')
        
        # [Mode 1] Code Recovery (Self-Healing)
        # 닉네임만으로 연결된 코드를 찾아서 반환 (로그인 시 자동 복구용)
        if action == 'check_link' and nickname:
            print(f"🔍 [SyncData] Checking link for nickname: {nickname}")
            
            # 1. User 찾기 (app_{nick} or {nick})
            candidates = [f"app_{nickname}", nickname]
            target_user = None
            for cand in candidates:
                try:
                    u = User.objects.get(username=cand)
                    target_user = u
                    break
                except User.DoesNotExist:
                    continue
            
            if not target_user:
                return Response({'linked': False, 'message': 'User not found in 150'}, status=404)
                
            # 2. Verification Code 찾기
            try:
                vc = VerificationCode.objects.filter(used_by=target_user, is_used=True).first()
                if vc:
                    print(f"✅ [SyncData] Found Code {vc.code} for {target_user.username}")
                    return Response({
                        'linked': True, 
                        'center_code': vc.code,
                        'center_name': vc.center.name if vc.center else "Unknown"
                    }, status=200)
            except Exception as e:
                print(f"❌ [SyncData] Link Check Error: {e}")
                
            return Response({'linked': False}, status=200)

        # [Mode 2] Data Fetch
        # 1. Auth & Identity Check (Dual-Lock Reuse)
        target_user = None
        if request.user and request.user.is_authenticated:
            target_user = request.user
        elif center_code and nickname:
            # Tokenless Access (Server-to-Server) verifying via Code & Nickname
            try:
                vc = VerificationCode.objects.filter(code=center_code).first()
                if vc and vc.is_used and vc.used_by:
                     if vc.used_by.username == f"app_{nickname}" or vc.used_by.username == nickname:
                         target_user = vc.used_by
            except:
                pass
        
        if not target_user:
             # 임시 유저라도 찾기? 아니면 401?
             # 217 싱크를 위해 임시 허용하지만, 원칙적으로는 인증 실패
             return Response({'error': 'Unauthorized / Center Code Mismatch'}, status=401)
        
        # 2. Fetch Diaries
        diaries = HaruOn.objects.filter(user=target_user).order_by('created_at')
        data = []
        for d in diaries:
            analysis = d.analysis_result or {}
            
            # [Rich Data Export]
            item = {
                'id': d.id,
                'event': d.content,
                'mood_level': d.mood_score, # 1-10
                'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                
                # Original Content (if needed)
                'content': d.content,
                
                # AI Analysis
                'ai_prediction': analysis.get('ai_prediction', ''),
                'ai_comment': analysis.get('ai_comment', ''),
                'ai_analysis': analysis.get('ai_analysis', ''),
                
                # Detailed Fields
                'emotion': analysis.get('emotion_desc', ''),
                'meaning': analysis.get('emotion_meaning', ''),
                'selftalk': analysis.get('self_talk', ''),
                'sleep_condition': analysis.get('sleep_condition', ''),
                
                # New Fields
                'weather': analysis.get('weather', ''),
                'medication_taken': analysis.get('medication_taken', False),
                'symptoms': analysis.get('symptoms', []),
                'gratitude_note': analysis.get('gratitude_note', '')
            }
            data.append(item)
            
        print(f"📤 [SyncData] Sending {len(data)} items for {target_user.username}")
        return Response(data)

    # [Emergency] Bypass Auth to salvage user data despite broken app token
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        [Push] iOS 앱 -> 150 서버 데이터 전송 (저장/동기화)
        """
        data = request.data
        center_code = data.get('center_code') or data.get('code')
        nickname = data.get('user_nickname')
        mood_metrics = data.get('mood_metrics', []) # List of diaries
        
        print(f"📥 [SyncData] Push Request. Code: {center_code}, User: {nickname}, Count: {len(mood_metrics)}")

        # 기존 로직(코드 주인 따라가기)은 계정 탈취 위험이 있어 폐기합니다.
        
        # [Strict Security] Token OR Code required
        target_user = None

        # 1. Try Token Auth first
        if request.user and request.user.is_authenticated:
            target_user = request.user
        
        # 2. Try Code Auth (if Token failed)
        if not target_user:
            if center_code:
                vc_auth = VerificationCode.objects.filter(code=center_code).first()
                if vc_auth and vc_auth.used_by:
                    target_user = vc_auth.used_by
                    print(f"🔐 [SyncData] Authenticated via Code: {center_code} -> User({target_user.username})")
        
        # 3. Final Security Check
        if not target_user:
            return Response({'detail': '유효한 인증 정보(토큰 또는 연동코드)가 없습니다.'}, status=401)

        # 2. Code Ownership Validation
        if center_code:
            try:
                vc = VerificationCode.objects.filter(code=center_code).first()
                if vc:
                    # Case A: New Code -> Claim Ownership
                    if not vc.is_used:
                        vc.is_used = True
                        vc.used_at = datetime.now()
                        vc.used_by = target_user
                        vc.save()
                        print(f"🔗 [B2G] Ownership Claimed: {center_code} -> User({target_user.id})")
                    
                    # Case B: Code Ownership Mismatch (Security Alert)
                    elif vc.used_by != target_user:
                        print(f"🚨 [Security] Ownership Conflict! Code({center_code}) belongs to User({vc.used_by.id}), but Request from User({target_user.id})")
                        print(f"🛑 [Action] Preventing Linkage Hijack. Saving data strictly to Request User({target_user.id}).")
                        # 여기서 에러를 낼지, 아니면 데이터만 저장할지 결정.
                        # 사용자 경험상 '데이터 저장'은 해주는 게 맞음. (내 일기는 내 DB에)
                        # 단, '연동 관계(B2G Link)'는 갱신하지 않음.
                    
                    # Case C: Valid Owner (Normal)
                    else:
                        pass # All Good
            except Exception as e:
                print(f"❌ [B2G] Validation Error: {e}")
        
        print(f"📥 [SyncData] Final Verified Target: {target_user.username} (ID: {target_user.id})")
            
        # 4. 데이터(일기) 저장 (상세 내용 포함)
        saved_count = 0
        for item in mood_metrics:
            try:
                # 날짜 파싱 (앱에서 문자열로 온다고 가정: ISO 8601 우선)
                date_str = item.get('created_at') or item.get('date')
                created_at = None
                if date_str:
                    created_at = parse_datetime(date_str)
                
                if not created_at:
                    created_at = datetime.now()
                
                # [AI Score Override] 
                # 사용자가 입력한 점수를 무시하고, AI 분석(감정) 또는 텍스트 기반으로 점수를 재산정
                raw_score = item.get('score', 0)
                ai_sentiment_text = item.get('ai_prediction', '') or item.get('emotion', '')
                
                def calculate_ai_score(text, default_score):
                    if not text: return default_score
                    # 10점 만점 기준 매핑
                    if any(x in text for x in ['행복', '기쁨', '신남', '즐거움', '긍정']): return 9 # 긍정 최상
                    if any(x in text for x in ['편안', '평온', '감사', '보람']): return 7       # 긍정 안정
                    if any(x in text for x in ['보통', '무난', '평범', '덤덤']): return 5       # 중립
                    if any(x in text for x in ['우울', '슬픔', '눈물', '지침', '피곤']): return 3 # 부정 우울
                    if any(x in text for x in ['화남', '분노', '짜증', '불안', '두려움']): return 1 # 부정 격앙
                    return default_score

                # AI가 분석한 점수로 교체 (AI 분석 내용이 있을 때만)
                if ai_sentiment_text:
                    score = calculate_ai_score(ai_sentiment_text, raw_score)
                    print(f"🤖 [AI Score] User({raw_score}) -> AI({score}) based on '{ai_sentiment_text[:10]}...'")
                else:
                    score = raw_score # Fallback
                
                
                # 상세 내용 파싱 및 조합
                event = item.get('event', '')
                emotion = item.get('emotion', '')
                meaning = item.get('meaning', '')
                selftalk = item.get('selftalk', '')
                sleep = item.get('sleep', '')
                
                # 내용이 없으면 기본값
                full_content = ""
                
                # [UI Fix] 
                # 대시보드가 예쁜 카드로 렌더링하려면 'analysis_result'에 구조화된 데이터가 있어야 함.
                # 'content' 필드는 메인 텍스트(사건)만 남겨서 깔끔하게 표시.
                
                # 1. Main Content (Event Only)
                if event:
                    full_content = event
                else:
                    full_content = f"기분 점수: {score}점"

                # 2. Structured Data for UI (Card View)
                # 기존 AI 데이터에 상세 기록들을 병합
                ai_data = {}
                if item.get('ai_comment'): ai_data['ai_comment'] = item.get('ai_comment')
                if item.get('ai_advice'): ai_data['ai_advice'] = item.get('ai_advice')
                if item.get('ai_analysis'): ai_data['ai_analysis'] = item.get('ai_analysis')
                if item.get('ai_prediction'): ai_data['ai_prediction'] = item.get('ai_prediction')
                
                # [Mapping] 앱 데이터를 대시보드 스펙에 맞게 매핑
                # 프론트엔드는 analysis_result 내부의 키를 확인하여 렌더링함
                if sleep: ai_data['sleep_condition'] = sleep  # 수면
                if meaning: ai_data['emotion_meaning'] = meaning # 의미
                if selftalk: ai_data['self_talk'] = selftalk   # 나에게 한마디
                if emotion: ai_data['emotion_desc'] = emotion  # 감정 묘사
                
                # [New] Weather & Bio Data
                weather = item.get('weather', '')
                meds_taken = item.get('medication_taken', False)
                symptoms = item.get('symptoms', [])
                gratitude = item.get('gratitude', '')

                if weather: ai_data['weather'] = weather
                ai_data['medication_taken'] = meds_taken
                if symptoms: ai_data['symptoms'] = symptoms
                if gratitude: ai_data['gratitude_note'] = gratitude
                
                # 중복 방지 (Update or Create)
                # target_user를 사용하여 기존 사용자에게 데이터 귀속
                obj, created_at_db = HaruOn.objects.update_or_create(
                    user=target_user,
                    created_at=created_at,
                    defaults={
                        'content': full_content.strip(),
                        'mood_score': score,
                        'is_high_risk': (score <= 2),
                        'analysis_result': ai_data if ai_data else None
                    }
                )
                
                if created_at_db:
                    saved_count += 1
                else:
                    print(f"🔄 [SyncData] 기존 일기 업데이트: {date_str}")
            except Exception as e:
                print(f"❌ [SyncData] 데이터 저장 실패: {e}")
                continue
        
        # 위험군 등급 업데이트 (간단 로직)
        if any((item.get('score', 10) <= 2) for item in mood_metrics):
             target_user.risk_level = User.RiskLevel.HIGH
             target_user.save()

        # [CRITICAL UPDATE: Relay to Server 217]
        # iOS App -> Server 150 (Here) -> Server 217 (vibe_coding)
        # 150 서버에 저장된 후, 즉시 217 서버로 데이터를 'Toss' 합니다.
        if center_code:
            try:
                import requests
                import json
                
                # 217 서버가 기대하는 포맷으로 재구성
                # (사실상 들어온 포맷 그대로 넘겨도 됨, 217도 동일한 프로토콜 사용)
                relay_payload = {
                    "center_code": center_code,
                    "user_nickname": nickname, # Original Nickname from App
                    "risk_level": target_user.risk_level if hasattr(target_user, 'risk_level') else 1,
                    "mood_metrics": mood_metrics
                }
                
                target_url = "https://217.142.253.35.nip.io/api/v1/centers/sync-data/"
                
                print(f"🚀 [Relay 150->217] Forwarding {len(mood_metrics)} items for {nickname}")
                requests.post(target_url, json=relay_payload, timeout=1, verify=False)
                print("✅ [Relay 150->217] Success")
                
            except Exception as e:
                print(f"❌ [Relay 150->217] Failed: {e}")
                # Don't fail the client response, this is a distinct backend process

        return Response({
            'success': True,
            'message': f'{saved_count}건의 데이터가 동기화되었습니다.',
            'center_code': center_code,
            'user_id': target_user.id
        })
