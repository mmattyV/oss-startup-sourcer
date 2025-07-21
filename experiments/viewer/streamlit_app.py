import streamlit as st # type: ignore
import boto3 # type: ignore
import pandas as pd # type: ignore
from typing import List, Dict, Any
from datetime import datetime
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore

# Page configuration
st.set_page_config(
    page_title="VC Startup Sourcer Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for attractive styling
st.markdown("""
<style>
    /* Main stats cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        margin: 0.5rem;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
    }
    
    .metric-card h3 {
        color: white;
        margin: 0;
        font-size: 0.9rem;
        font-weight: 600;
        opacity: 0.9;
    }
    
    .metric-card h1 {
        color: white;
        margin: 0.5rem 0 0 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    /* Repository cards */
    .repo-container {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 2px solid #667eea;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
        backdrop-filter: blur(5px);
        position: relative;
        overflow: hidden;
    }
    
    .repo-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Score badge */
    .score-badge {
        background: linear-gradient(45deg, #ff6b6b, #ffa726);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 30px;
        font-weight: bold;
        font-size: 1.3rem;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        border: 2px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Rank badges */
    .rank-badge {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.8rem;
        margin: 0 auto 1rem auto;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        border: 3px solid rgba(255,255,255,0.3);
    }
    
    /* Chart container */
    .chart-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_dynamodb_data(limit: int = 50) -> List[Dict[str, Any]]:
    """Load data from DynamoDB with caching."""
    try:
        session = boto3.Session(profile_name='root')
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table("vc-sourcing-analysis")
        
        response = table.scan()
        items = response['Items']
        
        # Sort by final_score in descending order
        sorted_items = sorted(items, key=lambda x: float(x.get('final_score', 0)), reverse=True)
        
        return sorted_items[:limit]
        
    except Exception as e:
        st.error(f"Error loading data from DynamoDB: {e}")
        return []

def format_repo_data(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format DynamoDB items for display."""
    formatted_repos = []
    
    for item in items:
        oss_data = item.get('oss_insight_data', {})
        repo_analysis = item.get('repo_analysis', {})
        community_analysis = item.get('community_analysis', {})
        
        repo_data = {
            'repo_name': item.get('repo_name', 'Unknown'),
            'final_score': float(item.get('final_score', 0)),
            'analysis_date': item.get('analysis_date', 'Unknown'),
            'stars': int(oss_data.get('stars', 0)),
            'total_score': float(oss_data.get('total_score', 0)),
            'description': oss_data.get('description', 'No description available'),
            'problem_clarity_score': int(repo_analysis.get('problem_clarity_score', 0)) if repo_analysis.get('problem_clarity_score') else None,
            'adoption_ease_score': int(repo_analysis.get('adoption_ease_score', 0)) if repo_analysis.get('adoption_ease_score') else None,
            'maturity_health_score': int(repo_analysis.get('maturity_health_score', 0)) if repo_analysis.get('maturity_health_score') else None,
            'problem_solved': repo_analysis.get('problem_solved', 'Not analyzed'),
            'excitement_score': int(community_analysis.get('excitement_score', 0)) if community_analysis.get('excitement_score') else None,
            'problem_solution_fit_score': int(community_analysis.get('problem_solution_fit_score', 0)) if community_analysis.get('problem_solution_fit_score') else None,
            'credibility_adoption_score': int(community_analysis.get('credibility_adoption_score', 0)) if community_analysis.get('credibility_adoption_score') else None,
            'key_praise_quote': community_analysis.get('key_praise_quote', ''),
            'main_criticism': community_analysis.get('main_criticism', '')
        }
        
        formatted_repos.append(repo_data)
    
    return formatted_repos

def create_score_visualization(repos: List[Dict[str, Any]]):
    """Create a score distribution chart."""
    df = pd.DataFrame(repos)
    
    # Clean up repository names for display
    df['display_name'] = df['repo_name'].str.replace('_', ' ').str.replace('-', ' ').str.title()
    
    fig = px.bar(
        df.head(10), 
        x='display_name', 
        y='final_score',
        title="Top 10 Repositories by VC Score",
        color='final_score',
        color_continuous_scale='viridis',
        labels={
            'display_name': 'Repository Name',
            'final_score': 'VC Score'
        }
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=False,
        xaxis_title="Repository Name",
        yaxis_title="VC Score"
    )
    
    return fig



def main():
    # Header with custom styling
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 3.5rem; font-weight: 700; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">
            🚀 VC Startup Sourcer Dashboard
        </h1>
        <p style="font-size: 1.2rem; color: #667eea; opacity: 0.8;">
            Discover the next big thing in DevOps & Infrastructure
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 📊 Dashboard Controls")
    limit = st.sidebar.slider("Number of repositories to display", 5, 50, 20)
    show_charts = st.sidebar.checkbox("Show visualization charts", True)
    show_detailed_metrics = st.sidebar.checkbox("Show detailed metrics", True)
    
    # Load data
    with st.spinner("Loading data from DynamoDB..."):
        raw_data = load_dynamodb_data(limit)
        repos = format_repo_data(raw_data)
    
    if not repos:
        st.error("No data available. Please check your DynamoDB connection.")
        return
    
    # Overview stats with gradient styling to match repository metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea, #764ba2); 
                   border-radius: 15px; margin: 1rem 0.5rem; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
            <div style="color: white; font-size: 2.2rem; font-weight: bold;">📋 {len(repos)}</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 1rem;">Total Repos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_score = sum(r['final_score'] for r in repos) / len(repos)
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #764ba2, #667eea); 
                   border-radius: 15px; margin: 1rem 0.5rem; box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3);">
            <div style="color: white; font-size: 2.2rem; font-weight: bold;">📊 {avg_score:.1f}</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 1rem;">Average Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_stars = sum(r['stars'] for r in repos)
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea, #764ba2); 
                   border-radius: 15px; margin: 1rem 0.5rem; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
            <div style="color: white; font-size: 2.2rem; font-weight: bold;">⭐ {total_stars:,}</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 1rem;">Total Stars</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        analyzed_repos = len([r for r in repos if r['problem_clarity_score'] is not None])
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #764ba2, #667eea); 
                   border-radius: 15px; margin: 1rem 0.5rem; box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3);">
            <div style="color: white; font-size: 2.2rem; font-weight: bold;">🔍 {analyzed_repos}/{len(repos)}</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 1rem;">Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Visualization
    if show_charts and repos:
        st.markdown("## 📈 Score Distribution")
        chart = create_score_visualization(repos)
        st.plotly_chart(chart, use_container_width=True)
    
    # Leaderboard
    st.markdown("## 🏆 Repository Leaderboard")
    
    for idx, repo in enumerate(repos, 1):
        
        # Create a boxed container using native Streamlit
        with st.container(border=True):
            # Header section with rank and repository name
            col_rank, col_title, col_score = st.columns([1, 4, 2])
            
            with col_rank:
                # Custom rank badge with gradients
                if idx == 1:
                    rank_gradient = "linear-gradient(135deg, #FFD700, #FFA500, #FFD700)"
                    rank_text_color = "#000"
                    shadow_color = "255, 215, 0"
                elif idx == 2:
                    rank_gradient = "linear-gradient(135deg, #E5E5E5, #C0C0C0, #E5E5E5)"
                    rank_text_color = "#000"
                    shadow_color = "192, 192, 192"
                elif idx == 3:
                    rank_gradient = "linear-gradient(135deg, #CD7F32, #A0522D, #CD7F32)"
                    rank_text_color = "#FFF"
                    shadow_color = "205, 127, 50"
                else:
                    rank_gradient = "linear-gradient(135deg, #667eea, #764ba2, #667eea)"
                    rank_text_color = "#FFF"
                    shadow_color = "102, 126, 234"
                
                st.markdown(f"""
                <div style="background: {rank_gradient}; color: {rank_text_color}; 
                           width: 60px; height: 60px; border-radius: 50%; 
                           display: flex; align-items: center; justify-content: center; 
                           font-weight: bold; font-size: 1.8rem; margin: 0 auto;
                           box-shadow: 0 6px 20px rgba({shadow_color}, 0.4), inset 0 2px 4px rgba(255,255,255,0.3);
                           border: 2px solid rgba(255,255,255,0.2);">
                    {idx}
                </div>
                """, unsafe_allow_html=True)
            
            with col_title:
                st.markdown(f"## {repo['repo_name']}")
            
            with col_score:
                # Custom score badge on the right
                st.markdown(f"""
                <div style="background: linear-gradient(45deg, #667eea, #764ba2); 
                           color: white; padding: 0.8rem 1.5rem; border-radius: 25px; 
                           font-weight: bold; font-size: 1.4rem; display: inline-block;
                           box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); margin-top: 0.5rem;">
                    🏆 {repo['final_score']:.1f}
                </div>
                """, unsafe_allow_html=True)
            
            # Add spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Repository metrics with custom styling and spacing
            col_stars, col_total = st.columns(2)
            with col_stars:
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea, #764ba2); 
                           border-radius: 15px; margin: 1rem 0.5rem; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
                    <div style="color: white; font-size: 2.2rem; font-weight: bold;">⭐ {repo['stars']:,}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 1rem;">Stars</div>
                </div>
                """, unsafe_allow_html=True)
            with col_total:
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #764ba2, #667eea); 
                           border-radius: 15px; margin: 1rem 0.5rem; box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3);">
                    <div style="color: white; font-size: 2.2rem; font-weight: bold;">📈 {repo['total_score']:,.0f}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 1rem;">Total Score</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Add more spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Description in a styled box with spacing
            st.info(f"**📋 Description:** {repo['description']}")
            
            # Problem solved in a styled box with spacing
            if repo['problem_solved'] and repo['problem_solved'] != 'Not analyzed':
                st.info(f"**🎯 Problem Solved:** {repo['problem_solved']}")
            
            # Add spacing before metrics
            st.markdown("<br>", unsafe_allow_html=True)
                
            # Add detailed metrics with custom styling and emojis
            if show_detailed_metrics and repo['problem_clarity_score'] is not None:
                st.markdown("### 📊 Repository Analysis")
                col_a, col_b, col_c = st.columns(3)
                
                metrics_data = [
                    ("🎯 Problem Clarity", repo['problem_clarity_score']),
                    ("⚡ Ease of Adoption", repo['adoption_ease_score']), 
                    ("💊 Project Maturity", repo['maturity_health_score'])
                ]
                
                for col, (label, value) in zip([col_a, col_b, col_c], metrics_data):
                    with col:
                        col.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: #667eea; 
                                   border-radius: 10px; margin: 0.5rem 0.2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                            <div style="color: white; font-size: 1.8rem; font-weight: bold;">{value}/5</div>
                            <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">{label}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add spacing
                st.markdown("<br>", unsafe_allow_html=True)
            
            if show_detailed_metrics and repo['excitement_score'] is not None:
                st.markdown("### 👥 Community Analysis")
                col_a, col_b, col_c = st.columns(3)
                
                community_data = [
                    ("😊 Community Excitement", repo['excitement_score']),
                    ("📈 Solution Fit", repo['problem_solution_fit_score']),
                    ("🏅 Credibility", repo['credibility_adoption_score'])
                ]
                
                for col, (label, value) in zip([col_a, col_b, col_c], community_data):
                    with col:
                        col.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: #27ae60; 
                                   border-radius: 10px; margin: 0.5rem 0.2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                            <div style="color: white; font-size: 1.8rem; font-weight: bold;">{value}/5</div>
                            <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">{label}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add spacing
                st.markdown("<br>", unsafe_allow_html=True)
            
            # Add quotes and criticism using native Streamlit components
            if repo['key_praise_quote']:
                st.success(f"**💬 Key Praise:** \"{repo['key_praise_quote']}\"")
            
            if repo['main_criticism']:
                st.warning(f"**⚠️ Main Criticism:** {repo['main_criticism']}")
            
            # Add spacing between repositories (no horizontal lines needed)
            st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>📊 VC Startup Sourcer Dashboard | Last updated: {}</p>
        <p>Data sourced from OSS Insight, GitHub, and community sentiment analysis</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)

if __name__ == "__main__":
    main() 