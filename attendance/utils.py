from typing import Dict, List, Any

def get_performance_insights(stats: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate personalized performance insights and tips for all modules.
    """
    insights = {
        'strengths': [],
        'improvements': [],
        'module_tips': {
            'attendance': [],
            'aptitude': [],
            'gd': [],
            'mock_interview': []
        }
    }

    # 1. Attendance Insights
    att_pct = stats.get('attendance_percentage', 0)
    if att_pct >= 90:
        insights['strengths'].append({'module': 'Attendance', 'text': 'Exceptional attendance record. You are showing great commitment.'})
        insights['module_tips']['attendance'].append('Maintain this consistency; it is a key trait highly valued by top-tier recruiters.')
    elif att_pct >= 75:
        insights['module_tips']['attendance'].append('You are above the eligibility threshold. Try to attend all remaining sessions to stay safe.')
    else:
        insights['improvements'].append({'module': 'Attendance', 'text': f'Attendance is low ({att_pct}%). Most companies require at least 75%.'})
        insights['module_tips']['attendance'].append('Prioritize attending physical sessions. Consistency is the first filter for placements.')

    # 2. Aptitude Insights
    apt_avg = stats.get('aptitude_stats', {}).get('avg_score', 0)
    total_tests = stats.get('aptitude_stats', {}).get('total_tests', 0)
    
    if total_tests < 3:
        insights['module_tips']['aptitude'].append('Take more aptitude tests to build speed and accuracy. Aim for at least 5 practice tests.')
    
    if apt_avg >= 80:
        insights['strengths'].append({'module': 'Aptitude', 'text': 'Strong logical and quantitative reasoning skills.'})
        insights['module_tips']['aptitude'].append('Practice higher-difficulty problems to stand out for Product-based company roles.')
    elif apt_avg >= 50:
        insights['module_tips']['aptitude'].append('Good progress. Focus on time management during tests to increase your score.')
    else:
        insights['improvements'].append({'module': 'Aptitude', 'text': 'Aptitude scores are currently below the competitive range.'})
        insights['module_tips']['aptitude'].append('Focus on fundamental concepts in Quant and Logical Reasoning. Use sectional tests for improvement.')

    # 3. GD Insights
    gd_avg = stats.get('gd_stats', {}).get('avg_score', 0)
    if gd_avg >= 8:
        insights['strengths'].append({'module': 'Group Discussion', 'text': 'Excellent communication and leadership in group settings.'})
        insights['module_tips']['gd'].append('Try to act as a moderator or concluder in discussions to showcase maturity.')
    elif gd_avg >= 5:
        insights['module_tips']['gd'].append('Work on structured thinking. Use the P-E-E-L (Point, Evidence, Explanation, Link) method.')
    else:
        insights['improvements'].append({'module': 'Group Discussion', 'text': 'Confidence or communication seems to be a barrier in GDs.'})
        insights['module_tips']['gd'].append('Start participating more. Even 2-3 quality points are better than staying silent.')

    # 4. Mock Interview Insights
    mi_analysis = stats.get('mock_interview_stats', {}).get('analysis', {})
    mi_completed = stats.get('mock_interview_stats', {}).get('completed', 0)
    
    if mi_completed == 0:
        insights['improvements'].append({'module': 'Interviews', 'text': 'No mock interviews completed. This is critical for final rounds.'})
        insights['module_tips']['mock_interview'].append('Schedule your first mock interview this week to overcome initial hesitation.')
    else:
        if mi_analysis.get('performance_level') == 'Excellent':
             insights['strengths'].append({'module': 'Interviews', 'text': 'Highly professional interview persona and technical clarity.'})
             insights['module_tips']['mock_interview'].append('Prepare for behavioral questions using the STAR method for bigger impact.')
        
        # Add weaknesses from MI analysis to improvements
        for weak in mi_analysis.get('weaknesses', []):
             insights['improvements'].append({'module': 'Interviews', 'text': f'Improve {weak.split("(")[0].strip()}'})
             
        # Add suggestions to tips
        for sug in mi_analysis.get('suggestions', []):
             insights['module_tips']['mock_interview'].append(sug)

    # 5. Generate Detailed Summary
    summary_parts = []
    
    # Analyze Overall Status
    prob = 0 # Re-calculate or use from stats if available
    # Actually, the view calculates probability, but we can summarize logically here.
    
    if stats.get('attendance_percentage', 0) < 75:
        summary_parts.append("Your low attendance is a critical risk factor that might disqualify you from several company drives.")
    
    if apt_avg < 60:
        summary_parts.append("Since your aptitude scores are below the competitive threshold, focusing on daily practice of logical and quantitative reasoning is highly recommended.")
    elif apt_avg > 80:
        summary_parts.append("Your strong aptitude scores make you a great candidate for high-paying product roles.")

    if gd_avg < 6:
        summary_parts.append("Your group discussion scores suggest some hesitation; consider joining communication workshops or practice sessions.")
    
    if mi_completed == 0:
        summary_parts.append("You haven't attempted any mock interviews yet. Completing at least one is essential to reduce final-round anxiety.")
    
    if not summary_parts:
        insights['detailed_summary'] = "Your performance across all training modules is exceptional and well-balanced. You are showing the dedication required for top-tier placements. Continue maintaining this level of consistency."
    else:
        insights['detailed_summary'] = " ".join(summary_parts)

    return insights
