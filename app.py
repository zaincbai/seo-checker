#!/usr/bin/env python3
"""
SEO Checker - Streamlit Web Interface
A beautiful web interface for the SEO analysis tool
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
import time
from datetime import datetime
import os
import json

# Import our SEO checker
from seo_checker import SEOChecker

# Configure Streamlit page
st.set_page_config(
    page_title="SEO Checker Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .url-result {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'urls_to_analyze' not in st.session_state:
        st.session_state.urls_to_analyze = []

def get_status_color(value, optimal_condition):
    """Get color for status indicators."""
    if optimal_condition:
        return "🟢"
    elif value:
        return "🟡"
    else:
        return "🔴"

def format_url_display(url):
    """Format URL for display."""
    if len(url) > 50:
        return url[:47] + "..."
    return url

def create_download_link(data, filename, file_type="csv"):
    """Create a download link for data."""
    if file_type == "csv":
        csv_data = data.to_csv(index=False)
        b64 = base64.b64encode(csv_data.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV Report</a>'
    else:  # JSON
        json_data = data.to_json(orient='records', indent=2)
        b64 = base64.b64encode(json_data.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="{filename}.json">Download JSON Report</a>'
    
    return href

def display_seo_metrics(result):
    """Display SEO metrics for a single URL."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Page Title",
            value=f"{result.get('title_length', 0)} chars",
            delta="Optimal" if result.get('title_optimal') else "Needs improvement"
        )
    
    with col2:
        st.metric(
            label="Meta Description",
            value=f"{result.get('meta_description_length', 0)} chars",
            delta="Optimal" if result.get('meta_description_optimal') else "Needs improvement"
        )
    
    with col3:
        st.metric(
            label="Word Count",
            value=f"{result.get('word_count', 0)} words",
            delta="Good" if result.get('content_length_optimal') else "Too short"
        )
    
    with col4:
        st.metric(
            label="Load Time",
            value=f"{result.get('load_time', 0):.2f}s",
            delta="Fast" if result.get('load_time', 0) < 3 else "Slow"
        )

def display_technical_seo(result):
    """Display technical SEO information."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**🔍 Technical SEO**")
        st.write(f"robots.txt: {'✅' if result.get('robots_txt_exists') else '❌'}")
        st.write(f"sitemap.xml: {'✅' if result.get('sitemap_xml_exists') else '❌'}")
        st.write(f"Canonical URL: {'✅' if result.get('canonical_exists') else '❌'}")
    
    with col2:
        st.write("**🏷️ Headings**")
        st.write(f"H1: {result.get('heading_counts', {}).get('h1_count', 0)} {'✅' if result.get('h1_optimal') else '❌'}")
        st.write(f"H2: {result.get('heading_counts', {}).get('h2_count', 0)}")
        st.write(f"H3: {result.get('heading_counts', {}).get('h3_count', 0)}")
    
    with col3:
        st.write("**📱 Social Media**")
        st.write(f"Open Graph: {result.get('og_tags_count', 0)} tags")
        st.write(f"Twitter Cards: {result.get('twitter_tags_count', 0)} tags")
        st.write(f"OG Image: {'✅' if result.get('has_og_image') else '❌'}")

def display_links_and_images(result):
    """Display links and images information."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔗 Links Analysis**")
        st.write(f"Total Links: {result.get('total_links', 0)}")
        st.write(f"Internal Links: {result.get('internal_links_count', 0)}")
        st.write(f"External Links: {result.get('external_links_count', 0)}")
        st.write(f"Broken Links: {result.get('broken_links_count', 0)}")
    
    with col2:
        st.write("**🖼️ Images Analysis**")
        st.write(f"Total Images: {result.get('total_images', 0)}")
        st.write(f"Missing Alt Text: {result.get('images_without_alt', 0)}")
        st.write(f"Empty Alt Text: {result.get('images_with_empty_alt', 0)}")
        if result.get('total_images', 0) > 0:
            optimization = result.get('images_alt_optimization', 0) * 100
            st.write(f"Alt Optimization: {optimization:.1f}%")

def create_seo_score_chart(results):
    """Create a comprehensive SEO score chart."""
    if not results:
        return None
    
    # Calculate SEO scores for each URL
    scores_data = []
    for result in results:
        if not result.get('analysis_successful'):
            continue
            
        # Calculate individual scores (0-100)
        title_score = 100 if result.get('title_optimal') else (50 if result.get('title_exists') else 0)
        meta_score = 100 if result.get('meta_description_optimal') else (50 if result.get('meta_description_exists') else 0)
        h1_score = 100 if result.get('h1_optimal') else (50 if result.get('has_h1') else 0)
        content_score = 100 if result.get('content_length_optimal') else 50
        technical_score = (
            (100 if result.get('robots_txt_exists') else 0) +
            (100 if result.get('sitemap_xml_exists') else 0) +
            (100 if result.get('canonical_exists') else 0)
        ) / 3
        
        # Images score
        total_images = result.get('total_images', 0)
        if total_images > 0:
            images_score = result.get('images_alt_optimization', 0) * 100
        else:
            images_score = 100  # No images is not necessarily bad
        
        # Social score
        social_score = (
            (100 if result.get('has_og_title') else 0) +
            (100 if result.get('has_og_description') else 0) +
            (100 if result.get('has_og_image') else 0)
        ) / 3
        
        # Overall score
        overall_score = (title_score + meta_score + h1_score + content_score + technical_score + images_score + social_score) / 7
        
        scores_data.append({
            'URL': format_url_display(result.get('url', '')),
            'Title': title_score,
            'Meta Desc': meta_score,
            'H1': h1_score,
            'Content': content_score,
            'Technical': technical_score,
            'Images': images_score,
            'Social': social_score,
            'Overall': overall_score
        })
    
    if not scores_data:
        return None
    
    df = pd.DataFrame(scores_data)
    
    # Create radar chart for the first URL or overall average
    if len(scores_data) == 1:
        # Single URL radar chart
        categories = ['Title', 'Meta Desc', 'H1', 'Content', 'Technical', 'Images', 'Social']
        values = [scores_data[0][cat] for cat in categories]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='SEO Score',
            line_color='#1f77b4'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="SEO Score Breakdown",
            height=400
        )
        
        return fig
    else:
        # Multiple URLs comparison chart
        fig = px.bar(
            df,
            x='URL',
            y='Overall',
            title='SEO Scores Comparison',
            color='Overall',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        
        fig.update_layout(
            xaxis_title="URLs",
            yaxis_title="SEO Score",
            height=400
        )
        
        return fig

def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🔍 SEO Checker Tool</h1>', unsafe_allow_html=True)
    st.markdown("**Comprehensive SEO analysis made simple**")
    
    # Sidebar
    st.sidebar.header("📋 Analysis Options")
    
    # Input method selection
    input_method = st.sidebar.radio(
        "Choose input method:",
        ["Enter URLs manually", "Upload URL file", "Use sample URLs"]
    )
    
    urls_to_analyze = []
    
    if input_method == "Enter URLs manually":
        st.sidebar.subheader("Enter URLs")
        url_input = st.sidebar.text_area(
            "Enter URLs (one per line):",
            height=150,
            placeholder="https://example.com\nhttps://yoursite.com"
        )
        
        if url_input:
            urls_to_analyze = [url.strip() for url in url_input.split('\n') if url.strip()]
    
    elif input_method == "Upload URL file":
        st.sidebar.subheader("Upload File")
        uploaded_file = st.sidebar.file_uploader(
            "Choose a file containing URLs",
            type=['txt', 'csv'],
            help="Upload a text file with one URL per line"
        )
        
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            urls_to_analyze = [url.strip() for url in content.split('\n') if url.strip() and not url.startswith('#')]
    
    else:  # Use sample URLs
        urls_to_analyze = [
            "https://example.com",
            "https://github.com",
            "https://stackoverflow.com"
        ]
        st.sidebar.info("Using sample URLs for demonstration")
    
    # Analysis settings
    st.sidebar.subheader("⚙️ Settings")
    log_level = st.sidebar.selectbox(
        "Log Level",
        ["INFO", "DEBUG", "WARNING", "ERROR"],
        index=0
    )
    
    # Display URLs to be analyzed
    if urls_to_analyze:
        st.sidebar.subheader("📝 URLs to Analyze")
        for i, url in enumerate(urls_to_analyze[:5], 1):
            st.sidebar.text(f"{i}. {format_url_display(url)}")
        
        if len(urls_to_analyze) > 5:
            st.sidebar.text(f"... and {len(urls_to_analyze) - 5} more")
        
        st.sidebar.info(f"Total URLs: {len(urls_to_analyze)}")
    
    # Main content area
    if not urls_to_analyze:
        st.info("👆 Please enter URLs in the sidebar to start analysis")
        
        # Show example of what the tool does
        st.subheader("🎯 What This Tool Analyzes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📊 SEO Metrics**
            - Page title optimization
            - Meta description analysis
            - Heading structure (H1-H6)
            - Content word count
            - Image alt text optimization
            - Internal/external links
            """)
        
        with col2:
            st.markdown("""
            **🔧 Technical SEO**
            - robots.txt detection
            - sitemap.xml verification
            - Canonical URL check
            - Page load time
            - Broken links detection
            - Social media tags
            """)
        
        return
    
    # Analysis button
    if st.sidebar.button("🚀 Start SEO Analysis", type="primary"):
        st.session_state.urls_to_analyze = urls_to_analyze
        st.session_state.analysis_complete = False
        st.session_state.analysis_results = []
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize SEO checker
        checker = SEOChecker(log_level=log_level)
        
        # Analyze URLs
        results = []
        for i, url in enumerate(urls_to_analyze):
            status_text.text(f"Analyzing {i+1}/{len(urls_to_analyze)}: {format_url_display(url)}")
            progress_bar.progress((i + 1) / len(urls_to_analyze))
            
            result = checker.analyze_url(url)
            results.append(result)
            
            # Small delay for UI updates
            time.sleep(0.1)
        
        # Store results
        st.session_state.analysis_results = results
        st.session_state.analysis_complete = True
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ Analysis complete! Analyzed {len(results)} URLs")
        st.rerun()
    
    # Display results
    if st.session_state.analysis_complete and st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        # Summary statistics
        st.subheader("📊 Analysis Summary")
        
        successful_analyses = sum(1 for r in results if r.get('analysis_successful'))
        failed_analyses = len(results) - successful_analyses
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total URLs", len(results))
        
        with col2:
            st.metric("Successful", successful_analyses, delta=f"{successful_analyses/len(results)*100:.1f}%")
        
        with col3:
            st.metric("Failed", failed_analyses)
        
        with col4:
            avg_load_time = sum(r.get('load_time', 0) for r in results if r.get('analysis_successful')) / max(successful_analyses, 1)
            st.metric("Avg Load Time", f"{avg_load_time:.2f}s")
        
        # SEO Score Visualization
        if successful_analyses > 0:
            st.subheader("📈 SEO Score Analysis")
            chart = create_seo_score_chart(results)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
        
        # Detailed results for each URL
        st.subheader("🔍 Detailed Results")
        
        for i, result in enumerate(results):
            if not result.get('analysis_successful'):
                st.error(f"❌ Failed to analyze: {result.get('url', 'Unknown URL')}")
                st.write(f"Error: {result.get('error', 'Unknown error')}")
                continue
            
            # Create expandable section for each URL
            with st.expander(f"🌐 {format_url_display(result.get('url', ''))} - Click to expand"):
                
                # Basic info
                st.write(f"**URL:** {result.get('url', 'N/A')}")
                st.write(f"**Status:** {result.get('status_code', 'N/A')}")
                st.write(f"**Load Time:** {result.get('load_time', 0):.2f}s")
                
                # SEO Metrics
                st.write("---")
                display_seo_metrics(result)
                
                # Technical SEO
                st.write("---")
                display_technical_seo(result)
                
                # Links and Images
                st.write("---")
                display_links_and_images(result)
                
                # Title and Meta Description
                if result.get('title'):
                    st.write("---")
                    st.write("**📝 Page Title:**")
                    st.write(result.get('title', 'N/A'))
                
                if result.get('meta_description'):
                    st.write("**📝 Meta Description:**")
                    st.write(result.get('meta_description', 'N/A'))
                
                # Headings structure
                headings = result.get('headings', {})
                if any(headings.values()):
                    st.write("---")
                    st.write("**🏷️ Headings Structure:**")
                    for level in ['h1', 'h2', 'h3']:
                        if headings.get(level):
                            st.write(f"**{level.upper()}:**")
                            for heading in headings[level][:3]:  # Show first 3 headings
                                st.write(f"- {heading}")
                            if len(headings[level]) > 3:
                                st.write(f"... and {len(headings[level]) - 3} more")
        
        # Download options
        st.subheader("💾 Download Reports")
        
        # Create DataFrame for download
        df_data = []
        for result in results:
            if result.get('analysis_successful'):
                df_data.append({
                    'URL': result.get('url', ''),
                    'Title': result.get('title', ''),
                    'Title Length': result.get('title_length', 0),
                    'Meta Description': result.get('meta_description', ''),
                    'Meta Description Length': result.get('meta_description_length', 0),
                    'H1 Count': result.get('heading_counts', {}).get('h1_count', 0),
                    'Word Count': result.get('word_count', 0),
                    'Total Images': result.get('total_images', 0),
                    'Images Without Alt': result.get('images_without_alt', 0),
                    'Total Links': result.get('total_links', 0),
                    'Internal Links': result.get('internal_links_count', 0),
                    'External Links': result.get('external_links_count', 0),
                    'Broken Links': result.get('broken_links_count', 0),
                    'Load Time': result.get('load_time', 0),
                    'Robots.txt': result.get('robots_txt_exists', False),
                    'Sitemap.xml': result.get('sitemap_xml_exists', False),
                    'OG Tags': result.get('og_tags_count', 0),
                    'Twitter Tags': result.get('twitter_tags_count', 0)
                })
        
        if df_data:
            df = pd.DataFrame(df_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📄 Download CSV Report",
                    data=csv,
                    file_name=f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Create a summary JSON
                summary = {
                    'analysis_date': datetime.now().isoformat(),
                    'total_urls': len(results),
                    'successful_analyses': successful_analyses,
                    'failed_analyses': failed_analyses,
                    'results': results
                }
                
                json_str = json.dumps(summary, indent=2)
                st.download_button(
                    label="📋 Download JSON Report",
                    data=json_str,
                    file_name=f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Reset button
        if st.button("🔄 Analyze New URLs"):
            st.session_state.analysis_complete = False
            st.session_state.analysis_results = []
            st.session_state.urls_to_analyze = []
            st.rerun()

if __name__ == "__main__":
    main() 