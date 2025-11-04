"""Text analysis utilities for extracting insights, topics, and sentiment."""

import asyncio
import logging
import re
import time
from collections import Counter
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import spacy
from textstat import flesch_reading_ease, flesch_kincaid_grade
import numpy as np

from mcp_server_article_quadrant.utils.error_handling import InsightAnalysisError, handle_error


class TextAnalyzer:
    """Main text analyzer for extracting insights from article content."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_nltk()
        self._initialize_spacy()

    def _initialize_nltk(self):
        """Initialize NLTK components."""
        try:
            # Download required NLTK data
            nltk_packages = ['punkt', 'stopwords', 'vader_lexicon', 'wordnet']
            for package in nltk_packages:
                try:
                    nltk.data.find(f'tokenizers/{package}')
                except LookupError:
                    nltk.download(package, quiet=True)

            # Initialize components
            self.stop_words = set(stopwords.words('english'))
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            self.lemmatizer = WordNetLemmatizer()

            # Add Chinese stopwords if available
            try:
                chinese_stopwords = set([
                    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                    '自己', '这', '那', '它', '他', '她', '们', '这个', '那个', '什么', '怎么'
                ])
                self.stop_words.update(chinese_stopwords)
            except Exception:
                self.logger.warning("Chinese stopwords not added")

        except Exception as e:
            self.logger.error(f"Failed to initialize NLTK: {e}")
            raise InsightAnalysisError(f"NLTK initialization failed: {e}")

    def _initialize_spacy(self):
        """Initialize spaCy models."""
        try:
            # Try to load English model
            self.nlp_en = spacy.load("en_core_web_sm")
            self.nlp_zh = None

            # Try to load Chinese model if available
            try:
                self.nlp_zh = spacy.load("zh_core_web_sm")
            except OSError:
                self.logger.warning("Chinese spaCy model not available")

        except OSError:
            self.logger.error("spaCy models not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp_en = None
            self.nlp_zh = None
        except Exception as e:
            self.logger.error(f"Failed to initialize spaCy: {e}")
            self.nlp_en = None
            self.nlp_zh = None

    def _detect_language(self, text: str) -> str:
        """Detect text language."""
        try:
            from langdetect import detect
            lang = detect(text)
            return 'zh' if lang == 'zh-cn' or lang == 'zh' else lang
        except Exception:
            # Fallback to simple heuristics
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            total_chars = len(re.sub(r'\s', '', text))
            if total_chars > 0 and chinese_chars / total_chars > 0.3:
                return 'zh'
            return 'en'

    def _preprocess_text(self, text: str, language: str = 'en') -> List[str]:
        """Preprocess text for analysis."""
        try:
            # Convert to lowercase and tokenize
            if language == 'zh':
                # For Chinese, use character-level tokenization
                tokens = list(re.findall(r'[\u4e00-\u9fff]+', text.lower()))
                # Add English words if present
                english_words = re.findall(r'[a-zA-Z]+', text.lower())
                tokens.extend(english_words)
            else:
                tokens = word_tokenize(text.lower())

            # Remove stopwords and short words
            tokens = [
                token for token in tokens
                if token not in self.stop_words
                and len(token) > 2
                and token.isalpha()
            ]

            # Lemmatize (for English)
            if language == 'en':
                tokens = [self.lemmatizer.lemmatize(token) for token in tokens]

            return tokens

        except Exception as e:
            self.logger.error(f"Text preprocessing failed: {e}")
            return []

    def _extract_keywords(self, text: str, language: str = 'en', max_keywords: int = 20) -> List[Tuple[str, float]]:
        """Extract keywords using TF-IDF-like scoring."""
        try:
            tokens = self._preprocess_text(text, language)
            if not tokens:
                return []

            # Calculate word frequencies
            word_freq = Counter(tokens)
            total_words = len(tokens)

            # Calculate TF-IDF-like scores
            # Using simple frequency with length normalization
            keyword_scores = []
            for word, freq in word_freq.most_common(max_keywords * 2):  # Get more to filter later
                # Normalize by word length to favor longer, more meaningful words
                score = (freq / total_words) * len(word)
                keyword_scores.append((word, score))

            # Sort by score and return top keywords
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            return keyword_scores[:max_keywords]

        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return []

    def _extract_topics(self, text: str, language: str = 'en', max_topics: int = 10) -> List[Dict[str, Any]]:
        """Extract main topics from text."""
        try:
            # Get keywords
            keywords = self._extract_keywords(text, language, max_topics * 3)

            if not keywords:
                return []

            # Group related keywords into topics (simple clustering)
            topics = []
            used_keywords = set()

            for keyword, score in keywords[:max_topics]:
                if keyword in used_keywords:
                    continue

                # Find related keywords (simple word overlap)
                related_keywords = []
                for other_keyword, other_score in keywords:
                    if other_keyword in used_keywords:
                        continue
                    # Check if words share characters (simplified similarity)
                    if any(char in other_keyword for char in keyword) or len(set(keyword) & set(other_keyword)) >= 2:
                        related_keywords.append((other_keyword, other_score))
                        used_keywords.add(other_keyword)

                # Create topic
                topic_keywords = [keyword] + [kw for kw, _ in related_keywords[:5]]  # Limit related keywords
                topic_score = score + sum(s for _, s in related_keywords[:5])

                topics.append({
                    "topic": keyword.replace('_', ' ').title(),
                    "relevance": min(topic_score, 1.0),  # Normalize to 0-1
                    "keywords": topic_keywords,
                    "frequency": len([kw for kw, _ in keywords if kw in topic_keywords])
                })

                used_keywords.add(keyword)

                if len(topics) >= max_topics:
                    break

            return topics[:max_topics]

        except Exception as e:
            self.logger.error(f"Topic extraction failed: {e}")
            return []

    def _extract_key_points(self, text: str, language: str = 'en', max_points: int = 15) -> List[Dict[str, Any]]:
        """Extract key points from text."""
        try:
            # Split into sentences
            if language == 'zh':
                # Chinese sentence segmentation
                sentences = re.split(r'[。！？；]', text)
            else:
                sentences = sent_tokenize(text)

            # Filter sentences
            key_points = []
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) < 10 or len(sentence) > 500:  # Skip very short or long sentences
                    continue

                # Calculate sentence importance based on various factors
                importance = self._calculate_sentence_importance(sentence, sentences, i, language)

                # Get sentiment
                sentiment = self._analyze_sentiment(sentence)

                key_points.append({
                    "point": sentence,
                    "importance": importance,
                    "sentiment": sentiment,
                    "position": i,
                    "context": self._get_sentence_context(sentences, i)
                })

            # Sort by importance and return top points
            key_points.sort(key=lambda x: x["importance"], reverse=True)
            return key_points[:max_points]

        except Exception as e:
            self.logger.error(f"Key points extraction failed: {e}")
            return []

    def _calculate_sentence_importance(self, sentence: str, all_sentences: List[str], position: int, language: str) -> float:
        """Calculate importance score for a sentence."""
        try:
            importance = 0.0

            # Length factor (moderate length sentences are often more important)
            word_count = len(sentence.split())
            if 10 <= word_count <= 30:
                importance += 0.3
            elif 5 <= word_count <= 50:
                importance += 0.2

            # Position factor (first and last sentences are often important)
            total_sentences = len(all_sentences)
            if position == 0 or position == total_sentences - 1:
                importance += 0.3
            elif position < 3 or position > total_sentences - 4:
                importance += 0.2

            # Keyword density
            keywords = self._extract_keywords(sentence, language, 10)
            if keywords:
                importance += min(len(keywords) * 0.1, 0.4)

            # Contains important indicators
            important_words = ['important', 'significant', 'key', 'main', 'primary', 'crucial',
                             'important', '关键', '主要', '重要', '核心', '重要']
            if any(word.lower() in sentence.lower() for word in important_words):
                importance += 0.2

            # Contains numbers or statistics
            if re.search(r'\d+[%$]|\d+\.\d+|\b\d+\b', sentence):
                importance += 0.1

            return min(importance, 1.0)

        except Exception:
            return 0.5  # Default importance if calculation fails

    def _get_sentence_context(self, sentences: List[str], position: int) -> str:
        """Get context around a sentence."""
        try:
            start = max(0, position - 1)
            end = min(len(sentences), position + 2)
            context_sentences = sentences[start:end]
            return ' '.join(context_sentences)
        except Exception:
            return ""

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text."""
        try:
            scores = self.sentiment_analyzer.polarity_scores(text)
            compound = scores['compound']

            if compound >= 0.05:
                if compound >= 0.5:
                    return "very_positive"
                else:
                    return "positive"
            elif compound <= -0.05:
                if compound <= -0.5:
                    return "very_negative"
                else:
                    return "negative"
            else:
                return "neutral"

        except Exception:
            return "neutral"

    def _extract_entities(self, text: str, language: str = 'en') -> List[Dict[str, Any]]:
        """Extract named entities using spaCy."""
        try:
            entities = []

            # Choose appropriate spaCy model
            nlp = self.nlp_en if language == 'en' and self.nlp_en else self.nlp_zh

            if nlp:
                # Process text with spaCy
                doc = nlp(text)

                # Extract entities
                entity_counts = Counter()
                entity_positions = {}

                for ent in doc.ents:
                    if len(ent.text.strip()) > 1:  # Skip very short entities
                        entity_text = ent.text.strip()
                        entity_type = ent.label_
                        entity_counts[(entity_text, entity_type)] += 1
                        if (entity_text, entity_type) not in entity_positions:
                            entity_positions[(entity_text, entity_type)] = []

                        # Get character position (approximate)
                        start_char = ent.start_char
                        if start_char not in entity_positions[(entity_text, entity_type)]:
                            entity_positions[(entity_text, entity_type)].append(start_char)

                # Create entity objects
                for (entity_text, entity_type), frequency in entity_counts.most_common(50):
                    entities.append({
                        "entity": entity_text,
                        "type": entity_type,
                        "frequency": frequency,
                        "confidence": min(frequency / len(entity_counts), 1.0) if entity_counts else 0.5,
                        "positions": entity_positions.get((entity_text, entity_type), [])[:5]  # Limit positions
                    })

            else:
                # Fallback: simple entity extraction using regex patterns
                entities = self._extract_entities_fallback(text)

            return entities

        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            return []

    def _extract_entities_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Fallback entity extraction using regex patterns."""
        entities = []

        try:
            # Extract capitalized words (potential organizations/people)
            capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            for word in capitalized_words[:20]:  # Limit to avoid too many entities
                if len(word) > 2:
                    entities.append({
                        "entity": word,
                        "type": "ORG",  # Default to organization
                        "frequency": text.count(word),
                        "confidence": 0.6,
                        "positions": []
                    })

            # Extract dates
            dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', text)
            for date in set(dates[:10]):  # Unique dates, limit count
                entities.append({
                    "entity": date,
                    "type": "DATE",
                    "frequency": text.count(date),
                    "confidence": 0.8,
                    "positions": []
                })

            # Extract monetary amounts
            money = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|CNY|dollars?|yuan)', text, re.IGNORECASE)
            for amount in set(money[:10]):
                entities.append({
                    "entity": amount,
                    "type": "MONEY",
                    "frequency": text.count(amount),
                    "confidence": 0.9,
                    "positions": []
                })

        except Exception as e:
            self.logger.error(f"Fallback entity extraction failed: {e}")

        return entities

    def _calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate text statistics."""
        try:
            # Basic counts
            word_count = len(text.split())
            sentence_count = len(sent_tokenize(text)) if self._is_english(text) else len(re.split(r'[。！？；]', text))
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])

            # Readability scores (for English text)
            readability_score = None
            complexity_level = "unknown"
            avg_sentence_length = 0

            if self._is_english(text) and word_count > 0:
                try:
                    readability_score = flesch_reading_ease(text)
                    complexity_level = self._get_complexity_level(readability_score)
                    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
                except Exception:
                    pass

            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_sentence_length": avg_sentence_length,
                "readability_score": readability_score,
                "complexity_level": complexity_level
            }

        except Exception as e:
            self.logger.error(f"Text statistics calculation failed: {e}")
            return {
                "word_count": len(text.split()),
                "sentence_count": 1,
                "paragraph_count": 1,
                "avg_sentence_length": 0,
                "readability_score": None,
                "complexity_level": "unknown"
            }

    def _is_english(self, text: str) -> bool:
        """Check if text is primarily English."""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.sub(r'\s', '', text))
        return total_chars == 0 or chinese_chars / total_chars < 0.3

    def _get_complexity_level(self, readability_score: float) -> str:
        """Determine complexity level from readability score."""
        if readability_score >= 90:
            return "very_easy"
        elif readability_score >= 80:
            return "easy"
        elif readability_score >= 70:
            return "fairly_easy"
        elif readability_score >= 60:
            return "standard"
        elif readability_score >= 50:
            return "fairly_difficult"
        elif readability_score >= 30:
            return "difficult"
        else:
            return "very_difficult"

    async def analyze_text(
        self,
        content: Dict[str, Any],
        analysis_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform complete text analysis."""
        start_time = time.time()

        try:
            text = content.get('text', '')
            title = content.get('title', '')
            metadata = content.get('metadata', {})

            if not text or not text.strip():
                raise InsightAnalysisError("No text content provided for analysis")

            # Detect language
            language = analysis_options.get('language', 'auto')
            if language == 'auto':
                language = self._detect_language(text)

            # Analysis options
            extract_topics = analysis_options.get('extract_topics', True)
            sentiment_analysis = analysis_options.get('sentiment_analysis', True)
            key_entities = analysis_options.get('key_entities', True)
            include_statistics = analysis_options.get('include_statistics', True)
            max_insights = analysis_options.get('max_insights', 20)

            analysis_result = {
                "main_topics": [],
                "key_points": [],
                "entities": [],
                "overall_sentiment": None,
                "statistics": None
            }

            # Extract topics
            if extract_topics:
                topics = self._extract_topics(text, language, max_insights)
                analysis_result["main_topics"] = topics

            # Extract key points
            key_points = self._extract_key_points(text, language, max_insights)
            analysis_result["key_points"] = key_points

            # Extract entities
            if key_entities:
                entities = self._extract_entities(text, language)
                analysis_result["entities"] = entities

            # Analyze overall sentiment
            if sentiment_analysis:
                overall_sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
                compound_score = overall_sentiment_scores['compound']

                # Map compound score to label
                if compound_score >= 0.05:
                    if compound_score >= 0.5:
                        sentiment_label = "very_positive"
                    else:
                        sentiment_label = "positive"
                elif compound_score <= -0.05:
                    if compound_score <= -0.5:
                        sentiment_label = "very_negative"
                    else:
                        sentiment_label = "negative"
                else:
                    sentiment_label = "neutral"

                analysis_result["overall_sentiment"] = {
                    "polarity": compound_score,
                    "subjectivity": overall_sentiment_scores.get('neu', 0.5),
                    "label": sentiment_label,
                    "confidence": abs(compound_score)
                }

            # Calculate text statistics
            if include_statistics:
                stats = self._calculate_text_statistics(text)
                analysis_result["statistics"] = stats

            # Create analysis metadata
            processing_time = time.time() - start_time
            analysis_metadata = {
                "processing_time": processing_time,
                "confidence_score": self._calculate_overall_confidence(analysis_result),
                "language_detected": language,
                "model_version": "1.0.0",
                "analysis_methods": ["nltk", "textstat", "custom"],
                "options_used": analysis_options
            }

            # Generate summary
            summary = self._generate_analysis_summary(analysis_result, title)

            return {
                "success": True,
                "insights": analysis_result,
                "metadata": analysis_metadata,
                "summary": summary,
                "processing_time": processing_time
            }

        except Exception as e:
            self.logger.error(f"Text analysis failed: {e}")
            return handle_error(
                e,
                context={"content_length": len(content.get('text', '')), "options": analysis_options},
                logger=self.logger
            )

    def _calculate_overall_confidence(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the analysis."""
        try:
            confidence_factors = []

            # Topics confidence (based on relevance scores)
            if analysis_result.get("main_topics"):
                topic_confidence = np.mean([t.get("relevance", 0.5) for t in analysis_result["main_topics"]])
                confidence_factors.append(topic_confidence)

            # Key points confidence (based on importance scores)
            if analysis_result.get("key_points"):
                points_confidence = np.mean([p.get("importance", 0.5) for p in analysis_result["key_points"]])
                confidence_factors.append(points_confidence)

            # Entities confidence (based on entity confidence scores)
            if analysis_result.get("entities"):
                entity_confidence = np.mean([e.get("confidence", 0.5) for e in analysis_result["entities"]])
                confidence_factors.append(entity_confidence)

            # Sentiment confidence
            if analysis_result.get("overall_sentiment"):
                sentiment_confidence = analysis_result["overall_sentiment"].get("confidence", 0.5)
                confidence_factors.append(sentiment_confidence)

            # Calculate average confidence
            if confidence_factors:
                return min(np.mean(confidence_factors), 1.0)
            else:
                return 0.5

        except Exception:
            return 0.5

    def _generate_analysis_summary(self, analysis_result: Dict[str, Any], title: str) -> str:
        """Generate a brief summary of the analysis results."""
        try:
            summary_parts = []

            # Title
            if title:
                summary_parts.append(f"Analysis of '{title}'")

            # Main topics
            topics = analysis_result.get("main_topics", [])[:3]  # Top 3 topics
            if topics:
                topic_names = [t["topic"] for t in topics]
                summary_parts.append(f"Main topics: {', '.join(topic_names)}")

            # Key insights count
            key_points = analysis_result.get("key_points", [])
            if key_points:
                summary_parts.append(f"Identified {len(key_points)} key insights")

            # Entities
            entities = analysis_result.get("entities", [])
            if entities:
                summary_parts.append(f"Extracted {len(entities)} named entities")

            # Sentiment
            sentiment = analysis_result.get("overall_sentiment")
            if sentiment:
                sentiment_label = sentiment.get("label", "neutral")
                summary_parts.append(f"Overall sentiment: {sentiment_label.replace('_', ' ')}")

            return ". ".join(summary_parts) + "."

        except Exception:
            return "Analysis completed successfully."