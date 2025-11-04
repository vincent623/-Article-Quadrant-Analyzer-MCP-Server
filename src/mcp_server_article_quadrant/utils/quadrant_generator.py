"""Quadrant visualization utilities for generating 2x2 quadrant diagrams."""

import logging
import math
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from mcp_server_article_quadrant.utils.error_handling import QuadrantGenerationError, ValidationError, handle_error


class QuadrantGenerator:
    """Generate 2x2 quadrant visualizations with SVG."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _calculate_quadrant_position(self, x_value: float, y_value: float) -> str:
        """Calculate quadrant position based on coordinates."""
        if x_value > 0 and y_value > 0:
            return "Q1"  # Top-right
        elif x_value <= 0 and y_value > 0:
            return "Q2"  # Top-left
        elif x_value <= 0 and y_value <= 0:
            return "Q3"  # Bottom-left
        else:  # x_value > 0 and y_value <= 0
            return "Q4"  # Bottom-right

    def _insight_to_coordinates(
        self,
        insight_text: str,
        importance: float,
        sentiment: str,
        x_dimension: str,
        y_dimension: str
    ) -> Tuple[float, float]:
        """Convert insight attributes to quadrant coordinates."""
        try:
            # Normalize importance to 0-1 range
            importance = max(0, min(1, importance))

            # Map sentiment to -1 to 1 range
            sentiment_map = {
                "very_positive": 1.0,
                "positive": 0.5,
                "neutral": 0.0,
                "negative": -0.5,
                "very_negative": -1.0
            }
            sentiment_value = sentiment_map.get(sentiment, 0.0)

            # Determine x coordinate based on dimension
            if x_dimension == "importance":
                x = importance * 2 - 1  # Convert 0-1 to -1 to 1
            elif x_dimension == "sentiment":
                x = sentiment_value
            elif x_dimension == "novelty":
                # Novelty based on text uniqueness (simplified)
                x = min(len(set(insight_text.split())) / len(insight_text.split()) * 2 - 1, 1)
            elif x_dimension == "practicality":
                # Practicality based on concrete language (simplified)
                practical_words = ['implement', 'execute', 'build', 'create', 'develop', 'deploy']
                practical_score = sum(1 for word in practical_words if word in insight_text.lower()) / len(practical_words)
                x = practical_score * 2 - 1
            else:  # custom
                x = (importance + sentiment_value) / 2

            # Determine y coordinate based on dimension
            if y_dimension == "urgency":
                # Urgency based on time-sensitive words
                urgent_words = ['immediate', 'urgent', 'critical', 'now', 'asap', 'emergency']
                urgency_score = sum(1 for word in urgent_words if word in insight_text.lower()) / len(urgent_words)
                y = urgency_score * 2 - 1
            elif y_dimension == "impact":
                y = importance * 2 - 1
            elif y_dimension == "feasibility":
                # Feasibility based on complexity indicators
                complex_words = ['complex', 'difficult', 'challenging', 'hard', 'complicated']
                complexity_score = sum(1 for word in complex_words if word in insight_text.lower()) / len(complex_words)
                y = 1 - complexity_score * 2  # Reverse: less complex = more feasible
            elif y_dimension == "complexity":
                complex_words = ['complex', 'difficult', 'challenging', 'hard', 'complicated']
                complexity_score = sum(1 for word in complex_words if word in insight_text.lower()) / len(complex_words)
                y = complexity_score * 2 - 1
            else:  # custom
                y = (importance - sentiment_value) / 2

            # Ensure coordinates are within bounds
            x = max(-1, min(1, x))
            y = max(-1, min(1, y))

            return x, y

        except Exception as e:
            self.logger.warning(f"Failed to calculate coordinates for insight: {e}")
            return 0, 0  # Default to center

    def _classify_insights_to_quadrants(
        self,
        insights: List[Dict[str, Any]],
        x_dimension: str,
        y_dimension: str,
        max_insights_per_quadrant: int = 15
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Classify insights into quadrants."""
        quadrants = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}

        try:
            for insight in insights:
                # Extract insight attributes
                insight_text = insight.get("point", insight.get("content", ""))
                importance = insight.get("importance", 0.5)
                sentiment = insight.get("sentiment", "neutral")

                # Calculate coordinates
                x, y = self._insight_to_coordinates(insight_text, importance, sentiment, x_dimension, y_dimension)
                quadrant = self._calculate_quadrant_position(x, y)

                # Add coordinate information
                insight["x_position"] = x
                insight["y_position"] = y
                insight["quadrant"] = quadrant

                # Add to appropriate quadrant
                if len(quadrants[quadrant]) < max_insights_per_quadrant:
                    quadrants[quadrant].append(insight)

        except Exception as e:
            self.logger.error(f"Failed to classify insights to quadrants: {e}")
            raise QuadrantGenerationError(f"Insight classification failed: {e}")

        return quadrants

    def _get_color_scheme(self, scheme: str) -> Dict[str, str]:
        """Get color scheme for visualization."""
        schemes = {
            "professional": {
                "background": "#ffffff",
                "grid": "#e0e0e0",
                "axes": "#333333",
                "q1_fill": "#e3f2fd",  # Light blue
                "q2_fill": "#f3e5f5",  # Light purple
                "q3_fill": "#fff3e0",  # Light orange
                "q4_fill": "#e8f5e8",  # Light green
                "text": "#333333",
                "title": "#1a1a1a",
                "insight": "#1976d2",
                "insight_border": "#0d47a1"
            },
            "vibrant": {
                "background": "#fafafa",
                "grid": "#bdbdbd",
                "axes": "#212121",
                "q1_fill": "#ff9800",  # Orange
                "q2_fill": "#2196f3",  # Blue
                "q3_fill": "#4caf50",  # Green
                "q4_fill": "#f44336",  # Red
                "text": "#212121",
                "title": "#000000",
                "insight": "#7b1fa2",
                "insight_border": "#4a148c"
            },
            "monochrome": {
                "background": "#ffffff",
                "grid": "#cccccc",
                "axes": "#666666",
                "q1_fill": "#f5f5f5",
                "q2_fill": "#e0e0e0",
                "q3_fill": "#d0d0d0",
                "q4_fill": "#c0c0c0",
                "text": "#333333",
                "title": "#000000",
                "insight": "#555555",
                "insight_border": "#333333"
            }
        }

        return schemes.get(scheme, schemes["professional"])

    def _truncate_text(self, text: str, max_length: int = 50) -> str:
        """Truncate text to specified length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def _calculate_text_position(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        padding: int = 50
    ) -> Tuple[int, int]:
        """Convert normalized coordinates to pixel positions."""
        # Convert from -1 to 1 range to pixel coordinates
        center_x = width // 2
        center_y = height // 2

        # Calculate position (flip y-axis for SVG coordinates)
        pixel_x = center_x + int(x * (width // 2 - padding))
        pixel_y = center_y - int(y * (height // 2 - padding))

        return pixel_x, pixel_y

    def _generate_svg_quadrant(
        self,
        quadrants: Dict[str, List[Dict[str, Any]]],
        config: Dict[str, Any],
        options: Dict[str, Any]
    ) -> str:
        """Generate SVG quadrant visualization."""
        try:
            width = options.get("width", 500)
            height = options.get("height", 500)
            color_scheme = self._get_color_scheme(options.get("color_scheme", "professional"))
            show_grid = options.get("show_grid", True)
            show_legend = options.get("show_legend", True)
            show_labels = options.get("show_labels", True)
            title = config.get("title", "Quadrant Analysis")

            # Get axis configuration
            x_axis = config.get("x_axis", {})
            y_axis = config.get("y_axis", {})
            quadrant_labels = config.get("quadrant_labels", ["Q1", "Q2", "Q3", "Q4"])

            # Start SVG
            svg_parts = [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                f'<rect width="{width}" height="{height}" fill="{color_scheme["background"]}"/>',
                '<defs>',
                '<style>',
                '  .title { font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; }',
                '  .axis-label { font-family: Arial, sans-serif; font-size: 12px; fill: #666; }',
                '  .quadrant-label { font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; }',
                '  .insight { font-family: Arial, sans-serif; font-size: 10px; }',
                '  .grid-line { stroke: #e0e0e0; stroke-width: 1; stroke-dasharray: 2,2; }',
                '  .axis-line { stroke: #333; stroke-width: 2; }',
                '</style>',
                '</defs>'
            ]

            # Add title
            if title:
                svg_parts.append(f'<text x="{width//2}" y="25" text-anchor="middle" class="title" fill="{color_scheme["title"]}">{title}</text>')

            # Calculate dimensions
            padding = 60
            drawable_width = width - 2 * padding
            drawable_height = height - 2 * padding
            center_x = width // 2
            center_y = height // 2

            # Draw quadrants (background colors)
            quadrant_coords = {
                "Q1": (center_x, padding, center_x + drawable_width // 2, center_y),
                "Q2": (padding, padding, center_x, center_y),
                "Q3": (padding, center_y, center_x, center_y + drawable_height // 2),
                "Q4": (center_x, center_y, center_x + drawable_width // 2, center_y + drawable_height // 2)
            }

            quadrant_colors = {
                "Q1": color_scheme["q1_fill"],
                "Q2": color_scheme["q2_fill"],
                "Q3": color_scheme["q3_fill"],
                "Q4": color_scheme["q4_fill"]
            }

            for q_key, (x1, y1, x2, y2) in quadrant_coords.items():
                opacity = 0.3 if q_key in quadrants and quadrants[q_key] else 0.1
                svg_parts.append(
                    f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" '
                    f'fill="{quadrant_colors[q_key]}" opacity="{opacity}"/>'
                )

            # Draw grid
            if show_grid:
                # Vertical center line
                svg_parts.append(f'<line x1="{center_x}" y1="{padding}" x2="{center_x}" y2="{height-padding}" class="grid-line"/>')
                # Horizontal center line
                svg_parts.append(f'<line x1="{padding}" y1="{center_y}" x2="{width-padding}" y2="{center_y}" class="grid-line"/>')

            # Draw axes
            # X-axis
            svg_parts.append(f'<line x1="{padding}" y1="{center_y}" x2="{width-padding}" y2="{center_y}" class="axis-line"/>')
            # Y-axis
            svg_parts.append(f'<line x1="{center_x}" y1="{padding}" x2="{center_x}" y2="{height-padding}" class="axis-line"/>')

            # Add axis arrows
            arrow_size = 8
            # X-axis arrow
            svg_parts.append(f'<polygon points="{width-padding},{center_y} {width-padding-arrow_size},{center_y-arrow_size//2} {width-padding-arrow_size},{center_y+arrow_size//2}" fill="{color_scheme["axes"]}"/>')
            # Y-axis arrow
            svg_parts.append(f'<polygon points="{center_x},{padding} {center_x-arrow_size//2},{padding+arrow_size} {center_x+arrow_size//2},{padding+arrow_size}" fill="{color_scheme["axes"]}"/>')

            # Add axis labels
            if show_labels:
                # X-axis labels
                x_label = x_axis.get("label", "X Axis")
                x_min_label = x_axis.get("min_label", "Low")
                x_max_label = x_axis.get("max_label", "High")

                svg_parts.append(f'<text x="{width-padding}" y="{center_y+20}" text-anchor="end" class="axis-label">{x_max_label}</text>')
                svg_parts.append(f'<text x="{center_x}" y="{height-20}" text-anchor="middle" class="axis-label">{x_label}</text>')
                svg_parts.append(f'<text x="{padding}" y="{center_y+20}" text-anchor="start" class="axis-label">{x_min_label}</text>')

                # Y-axis labels
                y_label = y_axis.get("label", "Y Axis")
                y_min_label = y_axis.get("min_label", "Low")
                y_max_label = y_axis.get("max_label", "High")

                svg_parts.append(f'<text x="{center_x-20}" y="{padding+10}" text-anchor="end" class="axis-label">{y_max_label}</text>')
                svg_parts.append(f'<text x="20" y="{center_y}" text-anchor="middle" transform="rotate(-90 20 {center_y})" class="axis-label">{y_label}</text>')
                svg_parts.append(f'<text x="{center_x-20}" y="{height-padding}" text-anchor="end" class="axis-label">{y_min_label}</text>')

                # Quadrant labels
                if len(quadrant_labels) == 4:
                    label_positions = [
                        (width - padding - 40, padding + 20),  # Q1
                        (padding + 40, padding + 20),          # Q2
                        (padding + 40, height - padding - 20), # Q3
                        (width - padding - 40, height - padding - 20) # Q4
                    ]
                    for i, (x, y) in enumerate(label_positions):
                        q_key = f"Q{i+1}"
                        label = quadrant_labels[i]
                        svg_parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" class="quadrant-label">{label}</text>')

            # Add insights
            for q_key, insights in quadrants.items():
                for insight in insights:
                    x_pos = insight.get("x_position", 0)
                    y_pos = insight.get("y_position", 0)
                    text = insight.get("point", insight.get("content", ""))
                    importance = insight.get("importance", 0.5)

                    # Calculate position
                    pixel_x, pixel_y = self._calculate_text_position(x_pos, y_pos, width, height, padding)

                    # Truncate text
                    display_text = self._truncate_text(text, 40)

                    # Size based on importance
                    font_size = max(8, int(10 + importance * 4))
                    circle_size = max(3, int(4 + importance * 4))

                    # Draw insight point
                    svg_parts.append(
                        f'<circle cx="{pixel_x}" cy="{pixel_y}" r="{circle_size}" '
                        f'fill="{color_scheme["insight"]}" stroke="{color_scheme["insight_border"]}" stroke-width="1"/>'
                    )

                    # Draw text
                    svg_parts.append(
                        f'<text x="{pixel_x + circle_size + 2}" y="{pixel_y + 3}" '
                        f'class="insight" fill="{color_scheme["text"]}">{display_text}</text>'
                    )

            # Add legend
            if show_legend:
                legend_y = height - 40
                legend_x = padding
                svg_parts.append('<g transform="translate(0, -10)">')
                svg_parts.append(f'<text x="{legend_x}" y="{legend_y}" class="axis-label">Quadrants:</text>')

                for i, (q_key, label) in enumerate(zip(["Q1", "Q2", "Q3", "Q4"], quadrant_labels[:4])):
                    x_pos = legend_x + 80 + i * 100
                    svg_parts.append(f'<rect x="{x_pos}" y="{legend_y-8}" width="12" height="12" fill="{quadrant_colors[q_key]}" opacity="0.5"/>')
                    svg_parts.append(f'<text x="{x_pos+16}" y="{legend_y}" class="axis-label">{label}</text>')

                svg_parts.append('</g>')

            # Close SVG
            svg_parts.append('</svg>')

            return '\n'.join(svg_parts)

        except Exception as e:
            self.logger.error(f"SVG generation failed: {e}")
            raise QuadrantGenerationError(f"SVG generation failed: {e}")

    def _calculate_quadrant_summary(
        self,
        quadrants: Dict[str, List[Dict[str, Any]]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate summary statistics for quadrant analysis."""
        try:
            total_insights = sum(len(insights) for insights in quadrants.values())
            dominant_quadrant = max(quadrants.keys(), key=lambda q: len(quadrants[q])) if quadrants else None

            # Find key findings
            key_findings = []
            for q_key, insights in quadrants.items():
                if insights:
                    count = len(insights)
                    key_findings.append(f"Quadrant {q_key} contains {count} insights")

            # Generate recommendations based on quadrant distribution
            recommendations = []
            if dominant_quadrant:
                if dominant_quadrant == "Q1":  # High-impact, high-effort
                    recommendations.append("Focus on strategic initiatives that require significant investment")
                elif dominant_quadrant == "Q2":  # High-impact, low-effort
                    recommendations.append("Prioritize quick wins that deliver high value")
                elif dominant_quadrant == "Q3":  # Low-impact, low-effort
                    recommendations.append("Consider if low-effort items are worth pursuing")
                elif dominant_quadrant == "Q4":  # Low-impact, high-effort
                    recommendations.append("Reevaluate high-effort, low-impact activities")

            return {
                "total_insights": total_insights,
                "dominant_quadrant": dominant_quadrant,
                "analysis_title": config.get("title", "Quadrant Analysis"),
                "key_findings": key_findings,
                "recommendations": recommendations,
                "quadrant_counts": {q: len(insights) for q, insights in quadrants.items()}
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate quadrant summary: {e}")
            return {
                "total_insights": 0,
                "dominant_quadrant": None,
                "analysis_title": config.get("title", "Quadrant Analysis"),
                "key_findings": [],
                "recommendations": [],
                "quadrant_counts": {}
            }

    async def generate_quadrant_analysis(
        self,
        insights: Dict[str, Any],
        quadrant_config: Dict[str, Any],
        visualization_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate complete quadrant analysis."""
        start_time = 0  # Will be set properly in real implementation

        try:
            # Validate inputs
            if not insights or not isinstance(insights, dict):
                raise ValidationError("Insights data is required and must be a dictionary")

            if not quadrant_config or not isinstance(quadrant_config, dict):
                raise ValidationError("Quadrant configuration is required and must be a dictionary")

            # Set default options
            options = visualization_options or {}
            default_options = {
                "width": 500,
                "height": 500,
                "color_scheme": "professional",
                "show_legend": True,
                "show_grid": True,
                "show_labels": True
            }
            options = {**default_options, **options}

            # Extract insight data
            key_points = insights.get("key_points", [])
            main_topics = insights.get("main_topics", [])
            entities = insights.get("entities", [])

            # Combine all insights for classification
            all_insights = []

            # Add key points
            for point in key_points:
                all_insights.append({
                    "content": point.get("point", ""),
                    "importance": point.get("importance", 0.5),
                    "sentiment": point.get("sentiment", "neutral"),
                    "type": "key_point"
                })

            # Add topics as insights
            for topic in main_topics:
                all_insights.append({
                    "content": f"Topic: {topic.get('topic', '')}",
                    "importance": topic.get("relevance", 0.5),
                    "sentiment": "neutral",
                    "type": "topic"
                })

            # Add top entities as insights
            for entity in entities[:10]:  # Limit to top 10 entities
                all_insights.append({
                    "content": f"Entity: {entity.get('entity', '')}",
                    "importance": min(entity.get("frequency", 1) / 10, 1.0),
                    "sentiment": "neutral",
                    "type": "entity"
                })

            if not all_insights:
                raise QuadrantGenerationError("No insights available for quadrant analysis")

            # Get axis configuration
            x_axis = quadrant_config.get("x_axis", {})
            y_axis = quadrant_config.get("y_axis", {})
            x_dimension = x_axis.get("dimension", "importance")
            y_dimension = y_axis.get("dimension", "impact")

            # Classify insights into quadrants
            quadrants = self._classify_insights_to_quadrants(
                all_insights,
                x_dimension,
                y_dimension
            )

            # Generate SVG visualization
            svg_content = self._generate_svg_quadrant(
                quadrants,
                quadrant_config,
                options
            )

            # Calculate summary
            summary = self._calculate_quadrant_summary(quadrants, quadrant_config)

            # Format quadrant data for output
            quadrant_data = []
            quadrant_labels = quadrant_config.get("quadrant_labels", ["Q1", "Q2", "Q3", "Q4"])

            for i, (q_key, insights) in enumerate(quadrants.items()):
                label = quadrant_labels[i] if i < len(quadrant_labels) else q_key

                # Find dominant theme in this quadrant
                dominant_theme = None
                if insights:
                    # Simple theme detection based on content frequency
                    content_words = []
                    for insight in insights[:5]:  # Top 5 insights
                        content_words.extend(insight.get("content", "").lower().split())

                    if content_words:
                        word_freq = {}
                        for word in content_words:
                            if len(word) > 3:  # Skip short words
                                word_freq[word] = word_freq.get(word, 0) + 1

                        if word_freq:
                            dominant_theme = max(word_freq, key=word_freq.get)

                quadrant_data.append({
                    "quadrant": q_key,
                    "label": label,
                    "insights": [
                        {
                            "content": insight.get("content", ""),
                            "x_position": insight.get("x_position", 0),
                            "y_position": insight.get("y_position", 0),
                            "quadrant": q_key,
                            "weight": insight.get("importance", 1.0),
                            "importance": insight.get("importance", 0.5),
                            "category": insight.get("type", "insight")
                        }
                        for insight in insights
                    ],
                    "count": len(insights),
                    "dominant_theme": dominant_theme
                })

            # Create result
            result = {
                "svg_content": svg_content,
                "quadrants": quadrant_data,
                "summary": summary,
                "config_used": quadrant_config,
                "visualization_options": options
            }

            processing_time = 0  # Would be calculated in real implementation

            return {
                "success": True,
                "quadrant_analysis": result,
                "metadata": {
                    "generated_at": "2024-01-01T00:00:00Z",  # Would be actual timestamp
                    "processing_time": processing_time,
                    "insights_processed": len(all_insights),
                    "quadrant_algorithm": "coordinate_based"
                }
            }

        except Exception as e:
            self.logger.error(f"Quadrant analysis failed: {e}")
            return handle_error(
                e,
                context={
                    "insights_count": len(insights.get("key_points", [])) if insights else 0,
                    "quadrant_config": quadrant_config,
                    "visualization_options": visualization_options
                },
                logger=self.logger
            )