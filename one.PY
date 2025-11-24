"""
Student Introduction Evaluator
Complete implementation in a single file
Author: Your Name
Date: November 2025

Requirements:
pip install streamlit pandas openpyxl vaderSentiment language-tool-python nltk

Usage:
streamlit run introduction_evaluator.py
"""

import re
import streamlit as st
import pandas as pd
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Try importing language_tool_python, provide fallback
try:
    import language_tool_python
    GRAMMAR_CHECK_AVAILABLE = True
except:
    GRAMMAR_CHECK_AVAILABLE = False
    st.warning("⚠️ Grammar checking unavailable. Install: pip install language-tool-python")


class IntroductionEvaluator:
    """Evaluates student self-introductions based on comprehensive rubrics"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        if GRAMMAR_CHECK_AVAILABLE:
            try:
                self.grammar_tool = language_tool_python.LanguageTool('en-US')
            except:
                self.grammar_tool = None
        else:
            self.grammar_tool = None
        
        # Salutation patterns
        self.salutations = {
            'excellent': ['excited to introduce', 'feeling great', 'thrilled', 'delighted'],
            'good': ['good morning', 'good afternoon', 'good evening', 'good day', 'hello everyone'],
            'normal': ['hi', 'hello', 'hey']
        }
        
        # Filler words list
        self.filler_words = ['um', 'uh', 'like', 'you know', 'so', 'actually', 'basically', 
                            'right', 'i mean', 'well', 'kinda', 'sort of', 'okay', 'hmm', 'ah']
        
        # Mandatory keywords (20 points total, 4 each)
        self.mandatory_keywords = {
            'name': ['name', 'myself', 'i am', "i'm", 'this is'],
            'age': ['years old', 'age', 'year old', 'old'],
            'school_class': ['school', 'class', 'grade', 'standard', 'studying'],
            'family': ['family', 'parents', 'father', 'mother', 'brother', 'sister', 'dad', 'mom'],
            'hobbies': ['hobby', 'hobbies', 'like to', 'enjoy', 'love', 'play', 'playing', 'interest']
        }
        
        # Optional keywords (10 points total, 2 each)
        self.optional_keywords = {
            'about_family': ['kind', 'loving', 'supportive', 'caring', 'special thing about'],
            'location': ['from', 'live in', 'belong to', 'city', 'town'],
            'ambition': ['want to', 'dream', 'goal', 'ambition', 'aspire', 'future', 'become'],
            'fun_fact': ['fun fact', 'interesting', 'unique', 'special', 'secret'],
            'achievements': ['achievement', 'won', 'award', 'accomplished', 'strength']
        }
    
    def evaluate(self, transcript, duration_seconds):
        """Main evaluation function"""
        transcript_lower = transcript.lower()
        
        results = {
            'content_structure': self._evaluate_content_structure(transcript, transcript_lower),
            'speech_rate': self._evaluate_speech_rate(transcript, duration_seconds),
            'language_grammar': self._evaluate_language_grammar(transcript, transcript_lower),
            'clarity': self._evaluate_clarity(transcript_lower),
            'engagement': self._evaluate_engagement(transcript)
        }
        
        # Calculate total score
        total_score = sum([
            results['content_structure']['total'],
            results['speech_rate']['score'],
            results['language_grammar']['total'],
            results['clarity']['score'],
            results['engagement']['score']
        ])
        
        results['total_score'] = total_score
        results['max_score'] = 100
        
        return results
    
    def _evaluate_content_structure(self, transcript, transcript_lower):
        """Evaluate content & structure (40 points)"""
        
        # 1. Salutation Level (5 points)
        salutation_score = 0
        salutation_type = "None"
        
        for level, patterns in self.salutations.items():
            if any(pattern in transcript_lower for pattern in patterns):
                if level == 'excellent':
                    salutation_score = 5
                    salutation_type = "Excellent"
                    break
                elif level == 'good' and salutation_score < 4:
                    salutation_score = 4
                    salutation_type = "Good"
                elif level == 'normal' and salutation_score < 2:
                    salutation_score = 2
                    salutation_type = "Normal"
        
        # 2. Keyword Presence - Mandatory (20 points, 4 each)
        mandatory_found = []
        mandatory_score = 0
        
        for key, patterns in self.mandatory_keywords.items():
            if any(pattern in transcript_lower for pattern in patterns):
                mandatory_found.append(key)
                mandatory_score += 4
        
        # 3. Keyword Presence - Optional (10 points, 2 each)
        optional_found = []
        optional_score = 0
        
        for key, patterns in self.optional_keywords.items():
            if any(pattern in transcript_lower for pattern in patterns):
                optional_found.append(key)
                optional_score += 2
        
        optional_score = min(optional_score, 10)  # Cap at 10
        
        # 4. Flow Analysis (5 points)
        flow_score = self._check_flow(transcript_lower)
        
        total = salutation_score + mandatory_score + optional_score + flow_score
        
        return {
            'salutation_score': salutation_score,
            'salutation_type': salutation_type,
            'mandatory_score': mandatory_score,
            'mandatory_found': mandatory_found,
            'optional_score': optional_score,
            'optional_found': optional_found,
            'flow_score': flow_score,
            'total': total,
            'max': 40
        }
    
    def _check_flow(self, transcript_lower):
        """Check if introduction follows proper flow"""
        sentences = re.split(r'[.!?]+', transcript_lower)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            return 3  # Partial credit for short intros
        
        # Check if salutation is at beginning
        has_greeting_first = any(pattern in sentences[0] for pattern in 
                                ['hello', 'hi', 'good morning', 'good afternoon', 'good evening'])
        
        # Check if name comes early (first 2 sentences)
        has_name_early = any(pattern in ' '.join(sentences[:2]) for pattern in 
                            ['name', 'myself', 'i am', "i'm"])
        
        # Check if closing exists
        has_closing = any(pattern in sentences[-1] for pattern in 
                         ['thank you', 'thanks', 'pleasure', 'nice to meet'])
        
        score = 0
        if has_greeting_first:
            score += 2
        if has_name_early:
            score += 2
        if has_closing:
            score += 1
        
        return min(score, 5)
    
    def _evaluate_speech_rate(self, transcript, duration_seconds):
        """Evaluate speech rate (10 points)"""
        words = transcript.split()
        word_count = len(words)
        
        if duration_seconds == 0:
            return {'score': 0, 'wpm': 0, 'category': 'Invalid', 'max': 10}
        
        wpm = (word_count / duration_seconds) * 60
        
        if wpm > 161:
            score = 2
            category = "Too Fast"
        elif 141 <= wpm <= 160:
            score = 6
            category = "Fast"
        elif 111 <= wpm <= 140:
            score = 10
            category = "Ideal ✓"
        elif 81 <= wpm <= 110:
            score = 6
            category = "Slow"
        else:  # < 80
            score = 2
            category = "Too Slow"
        
        return {
            'score': score,
            'wpm': round(wpm, 1),
            'word_count': word_count,
            'duration': duration_seconds,
            'category': category,
            'max': 10
        }
    
    def _evaluate_language_grammar(self, transcript, transcript_lower):
        """Evaluate language & grammar (20 points)"""
        
        # 1. Grammar Check (10 points)
        grammar_score = 10  # Default if tool unavailable
        error_count = 0
        
        if self.grammar_tool:
            try:
                matches = self.grammar_tool.check(transcript)
                error_count = len(matches)
                words = transcript.split()
                word_count = len(words)
                
                if word_count > 0:
                    errors_per_100 = (error_count / word_count) * 100
                    grammar_ratio = 1 - min(errors_per_100 / 10, 1)
                    
                    if grammar_ratio >= 0.9:
                        grammar_score = 10
                    elif grammar_ratio >= 0.7:
                        grammar_score = 8
                    elif grammar_ratio >= 0.5:
                        grammar_score = 6
                    elif grammar_ratio >= 0.3:
                        grammar_score = 4
                    else:
                        grammar_score = 2
            except:
                grammar_score = 10  # Fallback
        
        # 2. Vocabulary Richness - TTR (10 points)
        words = transcript_lower.split()
        unique_words = set(words)
        
        if len(words) > 0:
            ttr = len(unique_words) / len(words)
        else:
            ttr = 0
        
        if ttr >= 0.9:
            vocab_score = 10
        elif ttr >= 0.7:
            vocab_score = 8
        elif ttr >= 0.5:
            vocab_score = 6
        elif ttr >= 0.3:
            vocab_score = 4
        else:
            vocab_score = 2
        
        return {
            'grammar_score': grammar_score,
            'error_count': error_count,
            'vocab_score': vocab_score,
            'ttr': round(ttr, 3),
            'unique_words': len(unique_words),
            'total_words': len(words),
            'total': grammar_score + vocab_score,
            'max': 20
        }
    
    def _evaluate_clarity(self, transcript_lower):
        """Evaluate clarity - filler word rate (15 points)"""
        words = transcript_lower.split()
        total_words = len(words)
        
        if total_words == 0:
            return {'score': 0, 'filler_count': 0, 'filler_rate': 0, 'max': 15}
        
        filler_count = sum(1 for word in words if word in self.filler_words)
        filler_rate = (filler_count / total_words) * 100
        
        if filler_rate <= 3:
            score = 15
        elif filler_rate <= 6:
            score = 12
        elif filler_rate <= 9:
            score = 9
        elif filler_rate <= 12:
            score = 6
        else:
            score = 3
        
        return {
            'score': score,
            'filler_count': filler_count,
            'filler_rate': round(filler_rate, 2),
            'max': 15
        }
    
    def _evaluate_engagement(self, transcript):
        """Evaluate engagement - sentiment analysis (15 points)"""
        sentiment_scores = self.analyzer.polarity_scores(transcript)
        positive_score = sentiment_scores['pos']
        
        if positive_score >= 0.9:
            score = 15
        elif positive_score >= 0.7:
            score = 12
        elif positive_score >= 0.5:
            score = 9
        elif positive_score >= 0.3:
            score = 6
        else:
            score = 3
        
        return {
            'score': score,
            'positive_score': round(positive_score, 3),
            'sentiment_scores': sentiment_scores,
            'max': 15
        }


def main():
    """Streamlit UI"""
    st.set_page_config(page_title="Introduction Evaluator", page_icon="🎓", layout="wide")
    
    st.title("🎓 Student Introduction Evaluator")
    st.markdown("*Automated evaluation tool based on comprehensive rubrics*")
    
    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This tool evaluates student self-introductions based on:
        - **Content & Structure** (40 pts)
        - **Speech Rate** (10 pts)
        - **Language & Grammar** (20 pts)
        - **Clarity** (15 pts)
        - **Engagement** (15 pts)
        
        **Total: 100 points**
        """)
        
        st.header("📝 Sample Format")
        if st.button("Load Sample"):
            st.session_state.sample_loaded = True
    
    # Main input area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        transcript = st.text_area(
            "Enter Student Introduction Transcript:",
            height=200,
            placeholder="Hello everyone, myself...",
            value=st.session_state.get('sample_text', '')
        )
    
    with col2:
        duration = st.number_input(
            "Duration (seconds):",
            min_value=1,
            max_value=600,
            value=st.session_state.get('sample_duration', 60)
        )
    
    # Load sample button handler
    if st.session_state.get('sample_loaded'):
        st.session_state.sample_text = """Hello everyone, myself Muskan, studying in class 8th B section from Christ Public School. I am 13 years old. I live with my family. There are 3 people in my family, me, my mother and my father. One special thing about my family is that they are very kind hearted to everyone and soft spoken. One thing I really enjoy is play, playing cricket and taking wickets. A fun fact about me is that I see in mirror and talk by myself. One thing people don't know about me is that I once stole a toy from one of my cousin. My favorite subject is science because it is very interesting. Through science I can explore the whole world and make the discoveries and improve the lives of others. Thank you for listening."""
        st.session_state.sample_duration = 52
        st.session_state.sample_loaded = False
        st.rerun()
    
    # Evaluate button
    if st.button("🚀 Evaluate", type="primary"):
        if not transcript.strip():
            st.error("Please enter a transcript!")
            return
        
        with st.spinner("Analyzing..."):
            evaluator = IntroductionEvaluator()
            results = evaluator.evaluate(transcript, duration)
        
        # Display results
        st.success(f"## 🎯 Overall Score: {results['total_score']}/100")
        
        # Score breakdown
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Content", f"{results['content_structure']['total']}/40")
        with col2:
            st.metric("Speech Rate", f"{results['speech_rate']['score']}/10")
        with col3:
            st.metric("Language", f"{results['language_grammar']['total']}/20")
        with col4:
            st.metric("Clarity", f"{results['clarity']['score']}/15")
        with col5:
            st.metric("Engagement", f"{results['engagement']['score']}/15")
        
        # Detailed breakdown
        st.markdown("---")
        st.header("📊 Detailed Analysis")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Content & Structure", "Speech Rate", "Language & Grammar", "Clarity", "Engagement"
        ])
        
        with tab1:
            cs = results['content_structure']
            st.subheader(f"Score: {cs['total']}/40")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Salutation:** {cs['salutation_type']} ({cs['salutation_score']}/5)")
                st.write(f"**Flow:** {cs['flow_score']}/5")
            with col2:
                st.write(f"**Mandatory Keywords:** {cs['mandatory_score']}/20")
                st.write(f"**Optional Keywords:** {cs['optional_score']}/10")
            
            st.write("**Found Mandatory:** ", ', '.join(cs['mandatory_found']) if cs['mandatory_found'] else "None")
            st.write("**Found Optional:** ", ', '.join(cs['optional_found']) if cs['optional_found'] else "None")
        
        with tab2:
            sr = results['speech_rate']
            st.subheader(f"Score: {sr['score']}/10")
            st.write(f"**Words Per Minute:** {sr['wpm']} WPM")
            st.write(f"**Category:** {sr['category']}")
            st.write(f"**Word Count:** {sr['word_count']} words in {sr['duration']} seconds")
        
        with tab3:
            lg = results['language_grammar']
            st.subheader(f"Score: {lg['total']}/20")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Grammar:** {lg['grammar_score']}/10")
                st.write(f"**Errors Found:** {lg['error_count']}")
            with col2:
                st.write(f"**Vocabulary:** {lg['vocab_score']}/10")
                st.write(f"**TTR:** {lg['ttr']}")
                st.write(f"**Unique/Total Words:** {lg['unique_words']}/{lg['total_words']}")
        
        with tab4:
            cl = results['clarity']
            st.subheader(f"Score: {cl['score']}/15")
            st.write(f"**Filler Words:** {cl['filler_count']}")
            st.write(f"**Filler Rate:** {cl['filler_rate']}%")
        
        with tab5:
            eg = results['engagement']
            st.subheader(f"Score: {eg['score']}/15")
            st.write(f"**Positive Score:** {eg['positive_score']}")
            st.write("**Sentiment Breakdown:**")
            for key, val in eg['sentiment_scores'].items():
                st.write(f"  - {key}: {round(val, 3)}")
        
        # Feedback section
        st.markdown("---")
        st.header("💡 Feedback & Suggestions")
        
        feedback = []
        
        # Generate feedback based on scores
        if results['total_score'] >= 85:
            feedback.append("✅ **Excellent work!** Your introduction is well-crafted.")
        elif results['total_score'] >= 70:
            feedback.append("👍 **Good job!** Some areas can be improved.")
        else:
            feedback.append("📈 **Keep practicing!** There's room for improvement.")
        
        if results['content_structure']['total'] < 30:
            feedback.append("⚠️ Add more details about your family, hobbies, or goals.")
        
        if results['speech_rate']['score'] < 8:
            feedback.append(f"⚠️ Speech rate is {results['speech_rate']['category']}. Try to maintain 111-140 WPM.")
        
        if results['language_grammar']['vocab_score'] < 7:
            feedback.append("⚠️ Try using more diverse vocabulary.")
        
        if results['clarity']['filler_count'] > 0:
            feedback.append(f"⚠️ Reduce filler words (found {results['clarity']['filler_count']}).")
        
        if results['engagement']['score'] < 12:
            feedback.append("⚠️ Add more enthusiasm and positivity to your tone.")
        
        for item in feedback:
            st.markdown(item)


if __name__ == "__main__":
    main()
