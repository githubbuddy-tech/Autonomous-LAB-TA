"""Code analysis and comparison service"""
import difflib
import re
from typing import Dict, Any, List, Tuple
from ..models.embeddings import CodeEmbedding

class CodeAnalyzer:
    """Analyze and compare code"""
    
    def __init__(self):
        self.embedding_model = CodeEmbedding()
    
    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality and structure"""
        issues = []
        
        # Basic quality checks
        if not code.strip():
            return {
                "quality_score": 0,
                "issues": ["Empty code"],
                "suggestions": ["Write some code first"]
            }
        
        # Language-specific checks
        if language == "python":
            issues.extend(self._analyze_python(code))
        elif language == "java":
            issues.extend(self._analyze_java(code))
        elif language == "javascript":
            issues.extend(self._analyze_javascript(code))
        elif language == "c":
            issues.extend(self._analyze_c(code))
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(code, issues)
        
        return {
            "quality_score": quality_score,
            "issues": issues,
            "suggestions": self._generate_suggestions(issues, language)
        }
    
    def compare_code(self, student_code: str, reference_code: str, language: str) -> Dict[str, Any]:
        """Compare student code with reference solution"""
        if not reference_code:
            return {"error": "No reference code provided"}
        
        try:
            # 1. Syntax similarity (character level)
            syntax_similarity = difflib.SequenceMatcher(
                None, 
                student_code.strip(), 
                reference_code.strip()
            ).ratio()
            
            # 2. Logic similarity (based on structure)
            logic_similarity = self._calculate_logic_similarity(student_code, reference_code, language)
            
            # 3. Find specific differences
            differences = self._find_differences(student_code, reference_code, language)
            
            # 4. Calculate embedding similarity
            student_embedding = self.embedding_model.simple_embedding(student_code)
            reference_embedding = self.embedding_model.simple_embedding(reference_code)
            embedding_similarity = self.embedding_model.calculate_similarity(
                student_embedding, reference_embedding
            )
            
            # 5. Overall similarity (weighted average)
            overall_similarity = (syntax_similarity * 0.3 + 
                                 logic_similarity * 0.4 + 
                                 embedding_similarity * 0.3)
            
            return {
                "syntax_similarity": syntax_similarity,
                "logic_similarity": logic_similarity,
                "embedding_similarity": embedding_similarity,
                "overall_similarity": overall_similarity,
                "differences": differences,
                "match_percentage": overall_similarity * 100,
                "grade": self._calculate_grade(overall_similarity)
            }
            
        except Exception as e:
            return {"error": f"Comparison failed: {str(e)}"}
    
    def _analyze_python(self, code: str) -> List[str]:
        """Analyze Python code issues"""
        issues = []
        
        # Check for common errors
        if "pass" in code and "def " in code:
            issues.append("Function not implemented (using 'pass')")
        
        if "range(1," in code and "len(" in code:
            issues.append("Possible off-by-one error in range()")
        
        if "print(" not in code and "return " not in code:
            issues.append("No output or return statement")
        
        # Check for syntax errors
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('if ') and not line.rstrip().endswith(':'):
                issues.append(f"Missing colon in if statement (line {i+1})")
        
        return issues
    
    def _analyze_java(self, code: str) -> List[str]:
        """Analyze Java code issues"""
        issues = []
        
        if "public static void main" not in code:
            issues.append("Missing main method")
        
        if "System.out.println" not in code:
            issues.append("No print statements for output")
        
        return issues
    
    def _analyze_javascript(self, code: str) -> List[str]:
        """Analyze JavaScript code issues"""
        issues = []
        
        if "console.log" not in code:
            issues.append("No console output")
        
        return issues
    
    def _analyze_c(self, code: str) -> List[str]:
        """Analyze C code issues"""
        issues = []
        
        if "#include <stdio.h>" not in code and "printf" in code:
            issues.append("Missing stdio.h include for printf")
        
        return issues
    
    def _calculate_quality_score(self, code: str, issues: List[str]) -> int:
        """Calculate code quality score (0-10)"""
        score = 5  # Base score
        
        # Positive points
        if "#" in code or "//" in code:  # Comments
            score += 1
        
        if len(code.strip().split('\n')) > 3:  # Not too short
            score += 1
        
        if "def " in code or "function " in code or "public " in code:
            score += 2
        
        # Deduct for issues
        score -= min(len(issues), 5)
        
        return max(0, min(score, 10))
    
    def _generate_suggestions(self, issues: List[str], language: str) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        for issue in issues:
            if "not implemented" in issue.lower():
                suggestions.append("Implement the function logic instead of using placeholder")
            elif "off-by-one" in issue.lower():
                suggestions.append("Check array indices - remember they start at 0")
            elif "no output" in issue.lower():
                suggestions.append("Add print/return statements to see results")
        
        if language == "python":
            suggestions.append("Add docstrings to document your functions")
            suggestions.append("Consider edge cases in your code")
        
        return suggestions
    
    def _calculate_logic_similarity(self, code1: str, code2: str, language: str) -> float:
        """Calculate logic similarity between two code snippets"""
        # Extract structural elements
        def extract_elements(code: str, language: str) -> List[str]:
            elements = []
            
            if language == "python":
                # Count function definitions, loops, conditionals
                elements.append(f"funcs:{code.count('def ')}")
                elements.append(f"loops:{code.count('for ') + code.count('while ')}")
                elements.append(f"conditionals:{code.count('if ') + code.count('elif ') + code.count('else:')}")
                elements.append(f"returns:{code.count('return ')}")
            
            elif language == "java":
                elements.append(f"methods:{code.count('public ') + code.count('private ') + code.count('protected ')}")
                elements.append(f"loops:{code.count('for ') + code.count('while ')}")
                elements.append(f"conditionals:{code.count('if ') + code.count('else ')}")
                elements.append(f"returns:{code.count('return ')}")
            
            return elements
        
        elems1 = extract_elements(code1, language)
        elems2 = extract_elements(code2, language)
        
        # Simple matching
        matches = sum(1 for e1 in elems1 if e1 in elems2)
        total = max(len(elems1), len(elems2))
        
        return matches / total if total > 0 else 0.0
    
    def _find_differences(self, code1: str, code2: str, language: str) -> List[Dict[str, Any]]:
        """Find specific differences between codes"""
        differences = []
        
        lines1 = code1.strip().split('\n')
        lines2 = code2.strip().split('\n')
        
        diff = difflib.unified_diff(lines1, lines2, lineterm='')
        diff_list = list(diff)
        
        if len(diff_list) > 2:
            differences.append({
                "type": "structural_difference",
                "description": f"Found {len(diff_list)-2} line differences",
                "diff_output": '\n'.join(diff_list[2:])  # Skip header lines
            })
        
        return differences
    
    def _calculate_grade(self, similarity: float) -> str:
        """Calculate letter grade based on similarity"""
        if similarity >= 0.9:
            return "A"
        elif similarity >= 0.8:
            return "B"
        elif similarity >= 0.7:
            return "C"
        elif similarity >= 0.6:
            return "D"
        else:
            return "F"