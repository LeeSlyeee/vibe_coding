path = '/home/ubuntu/InsightMind/backend/maum_on/urls.py'
with open(path, 'r') as f:
    content = f.read()

# 1. Import 추가
if 'AssessmentView' not in content:
    content = content.replace('GetConfigView', 'GetConfigView, AssessmentView')

# 2. Path 추가
new_path = "    path('assessment/', AssessmentView.as_view(), name='assessment'),"
if 'assessment/' not in content:
    # statistics 라인 뒤에 추가
    target = "path('statistics/', StatisticsView.as_view(), name='statistics'),"
    if target in content:
        content = content.replace(target, target + '\n' + new_path)
    else:
        # target이 없으면 urlpatterns = [ 바로 뒤나 적당한 곳에...
        # 하지만 statistics는 방금 전 확인했으므로 있을 것임.
        pass

with open(path, 'w') as f:
    f.write(content)
