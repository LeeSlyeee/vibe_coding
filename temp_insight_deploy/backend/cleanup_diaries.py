from django.contrib.auth import get_user_model
from haru_on.models import HaruOn
import datetime

User = get_user_model()

def clean_duplicates(username):
    try:
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            print(f"User {username} not found")
            return

        all_diaries = HaruOn.objects.filter(user=u)
        # Group by date
        date_map = {}
        for d in all_diaries:
            # UTC Date usually.
            # Local Time issue aside, duplicates usually have SAME created_at string prefix or close enough
            # Use YYYY-MM-DD string
            d_date = d.created_at.strftime('%Y-%m-%d')
            if d_date not in date_map:
                date_map[d_date] = []
            date_map[d_date].append(d)
        
        for d_date, diaries in date_map.items():
            if len(diaries) > 1:
                print(f"Processing {d_date}: Found {len(diaries)} entries.")
                
                # Sort by ID (usually implies creation order)
                diaries.sort(key=lambda x: x.id)
                
                best = None
                best_score = -1
                
                # Score Logic: More keys = Better. 'weather' presence = Much Better.
                for d in diaries:
                    ar = d.analysis_result or {}
                    score = len(ar.keys())
                    if 'weather' in ar and ar['weather']: score += 10
                    if 'mood_score' in ar: score += 1
                    
                    # Tie-breaker: Newer ID is better
                    if score >= best_score:
                        best = d
                        best_score = score
                
                print(f"  Keeping ID {best.id} (Score {best_score})")
                
                for d in diaries:
                    if d.id != best.id:
                        print(f"  Deleting ID {d.id}...")
                        d.delete()
            else:
                pass
                # print(f"{d_date}: Single entry, skip.")

    except Exception as e:
        print(f"Error: {e}")

clean_duplicates('app_Guest')
