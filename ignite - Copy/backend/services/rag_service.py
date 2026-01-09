"""RAG (Retrieval-Augmented Generation) service - SQLite only version"""
import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional
from ..models.embeddings import CodeEmbedding

class RAGService:
    """Generate hints using simple RAG with SQLite"""
    
    def __init__(self, db_path: str = "data/labta.db"):
        self.db_path = db_path
        self.embedding_model = CodeEmbedding()
        self._init_database()
    
    def _init_database(self):
        """Initialize RAG database without vector DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create solutions table with simple similarity storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rag_solutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                language TEXT,
                code TEXT,
                error_type TEXT,
                hint TEXT,
                embedding_hash TEXT,  # Store hash instead of full embedding
                common_patterns TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rag_task_lang 
            ON rag_solutions(task_id, language)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rag_error_type 
            ON rag_solutions(error_type)
        ''')
        
        # Create patterns table for faster searching
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT,
                language TEXT,
                solution_count INTEGER DEFAULT 0,
                common_error TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ RAG database initialized")
    
    def generate_hint(self, student_code: str, error: str, 
                     language: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate hint using pattern matching"""
        try:
            # Extract patterns from student code
            patterns = self._extract_patterns(student_code, language)
            
            # Search for similar patterns
            similar_solutions = self._search_by_patterns(patterns, language, task_id, error)
            
            # Generate hint
            hint = self._generate_pattern_based_hint(student_code, error, similar_solutions)
            
            # Store for future learning
            self._store_solution_patterns(student_code, error, language, task_id, hint, patterns)
            
            return {
                "hint": hint,
                "similarity_score": similar_solutions[0]['score'] if similar_solutions else 0,
                "similar_solutions": similar_solutions[:2],
                "rag_used": True,
                "patterns_found": len(patterns)
            }
            
        except Exception as e:
            # Fallback to rule-based hint
            return {
                "hint": self._generate_rule_based_hint(error, language, student_code),
                "similarity_score": 0,
                "similar_solutions": [],
                "rag_used": False,
                "error": str(e)
            }
    
    def _extract_patterns(self, code: str, language: str) -> List[str]:
        """Extract code patterns for matching"""
        patterns = []
        
        # Basic pattern extraction
        lines = code.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Extract function definitions
            if language == "python" and line.startswith('def '):
                patterns.append('function_def:' + line.split('(')[0].replace('def ', ''))
            
            # Extract loops
            if 'for ' in line or 'while ' in line:
                patterns.append('loop_statement')
            
            # Extract conditionals
            if line.startswith('if ') or line.startswith('elif ') or 'else:' in line:
                patterns.append('conditional_statement')
            
            # Extract return statements
            if 'return ' in line:
                patterns.append('return_statement')
            
            # Extract variable assignments
            if ' = ' in line and not line.startswith('def '):
                var_name = line.split(' = ')[0].strip()
                if var_name:
                    patterns.append(f'var_assignment:{var_name}')
        
        return list(set(patterns))  # Remove duplicates
    
    def _search_by_patterns(self, patterns: List[str], language: str, 
                           task_id: Optional[str], error: str) -> List[Dict[str, Any]]:
        """Search for solutions matching patterns"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query based on patterns
        if not patterns:
            return []
        
        # Create pattern matching conditions
        pattern_conditions = []
        for pattern in patterns:
            if ':' in pattern:
                key, value = pattern.split(':', 1)
                if key == 'function_def':
                    pattern_conditions.append(f"code LIKE '%def {value}%'")
                elif key == 'var_assignment':
                    pattern_conditions.append(f"code LIKE '%{value} = %'")
            else:
                pattern_conditions.append(f"code LIKE '%{pattern}%'")
        
        # Build WHERE clause
        where_clause = f"language = '{language}'"
        if task_id:
            where_clause += f" AND task_id = '{task_id}'"
        if error:
            where_clause += f" AND error_type LIKE '%{error[:20]}%'"
        
        if pattern_conditions:
            where_clause += " AND (" + " OR ".join(pattern_conditions[:3]) + ")"
        
        query = f'''
            SELECT id, task_id, language, code, error_type, hint
            FROM rag_solutions
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT 5
        '''
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
        except:
            rows = []
        
        conn.close()
        
        # Calculate match scores
        solutions = []
        for row in rows:
            score = self._calculate_pattern_match_score(patterns, row['code'])
            if score > 0.1:  # Only include decent matches
                solutions.append({
                    "id": row['id'],
                    "task_id": row['task_id'],
                    "code": row['code'][:200] + "..." if len(row['code']) > 200 else row['code'],
                    "error_type": row['error_type'],
                    "hint": row['hint'],
                    "score": score
                })
        
        # Sort by score
        solutions.sort(key=lambda x: x['score'], reverse=True)
        return solutions
    
    def _calculate_pattern_match_score(self, patterns: List[str], code: str) -> float:
        """Calculate how well patterns match code"""
        if not patterns:
            return 0.0
        
        matches = 0
        for pattern in patterns:
            if ':' in pattern:
                key, value = pattern.split(':', 1)
                if key == 'function_def' and f'def {value}' in code:
                    matches += 2  # Function names are important
                elif key == 'var_assignment' and f'{value} = ' in code:
                    matches += 1
            elif pattern in code:
                matches += 1
        
        return matches / len(patterns) if patterns else 0.0
    
    def _generate_pattern_based_hint(self, student_code: str, error: str, 
                                    similar_solutions: List[Dict]) -> str:
        """Generate hint based on similar patterns"""
        if not similar_solutions:
            return self._generate_rule_based_hint(error, "python", student_code)
        
        best_match = similar_solutions[0]
        
        hint_parts = [
            f"Found similar code pattern ({best_match['score']:.0%} match):"
        ]
        
        # Add error-specific advice
        error_lower = error.lower()
        if any(word in error_lower for word in ['syntax', 'invalid']):
            hint_parts.append("• Check syntax: parentheses, brackets, colons")
            hint_parts.append("• Verify indentation is consistent")
        
        if 'not defined' in error_lower or 'name' in error_lower:
            hint_parts.append("• Check variable/function names for typos")
            hint_parts.append("• Make sure variables are declared before use")
        
        if 'index' in error_lower:
            hint_parts.append("• Check array/list bounds")
            hint_parts.append("• Remember indices start at 0")
        
        # Add code-specific advice
        if 'pass' in student_code:
            hint_parts.append("• Replace 'pass' with actual implementation")
        
        # Add example from similar solution
        if best_match['hint']:
            hint_parts.append(f"\nRelated hint from similar code:")
            hint_parts.append(f"\"{best_match['hint'][:200]}...\"")
        
        return '\n'.join(hint_parts)
    
    def _generate_rule_based_hint(self, error: str, language: str, code: str) -> str:
        """Generate hint based on rules"""
        hint = f"Debugging {language} code:\n"
        
        rules = {
            'python': [
                "1. Check for syntax errors (missing colons, parentheses)",
                "2. Verify indentation (use 4 spaces)",
                "3. Make sure variables are defined before use",
                "4. Check function names and arguments",
                "5. Use print() to debug variable values"
            ],
            'java': [
                "1. Check for missing semicolons ;",
                "2. Verify braces {} are balanced",
                "3. Make sure class and method names match",
                "4. Check variable types",
                "5. Ensure proper imports"
            ],
            'javascript': [
                "1. Check console for errors",
                "2. Verify variable declarations (let/const/var)",
                "3. Check function definitions and calls",
                "4. Look for undefined variables",
                "5. Check bracket/parenthesis matching"
            ],
            'c': [
                "1. Check #include statements",
                "2. Verify semicolons after statements",
                "3. Check function prototypes",
                "4. Look for uninitialized variables",
                "5. Check pointer usage"
            ]
        }
        
        lang_rules = rules.get(language, rules['python'])
        hint += '\n'.join(lang_rules)
        
        # Add code-specific advice
        if 'sum' in code.lower() and 'pass' in code:
            hint += "\n\nFor sum function: Implement the loop or use sum() function"
        
        return hint
    
    def _store_solution_patterns(self, code: str, error: str, language: str,
                                task_id: Optional[str], hint: str, patterns: List[str]):
        """Store solution patterns for future use"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store the full solution
            cursor.execute('''
                INSERT INTO rag_solutions 
                (task_id, language, code, error_type, hint, embedding_hash, common_patterns)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                language,
                code[:1000],
                error[:100] if error else "no_error",
                hint[:500],
                hash(code) % 1000000,  # Simple hash
                json.dumps(patterns[:10]) if patterns else "[]"
            ))
            
            # Update pattern frequencies
            for pattern in patterns[:5]:  # Limit to top 5 patterns
                cursor.execute('''
                    INSERT OR REPLACE INTO code_patterns (pattern, language, solution_count, common_error)
                    VALUES (?, ?, 
                        COALESCE((SELECT solution_count FROM code_patterns 
                                 WHERE pattern = ? AND language = ?), 0) + 1,
                        ?)
                ''', (pattern, language, pattern, language, error[:50] if error else "general"))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to store RAG patterns: {e}")