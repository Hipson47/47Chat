"""
Benchmark tests for performance-critical functions.
Uses pytest-benchmark to track performance regressions.
"""

import pytest
from backend.orchestrator.utils.team_assigner import auto_assign_teams


@pytest.fixture
def sample_meta_prompt():
    """Sample meta prompt with multiple teams for benchmarking."""
    return {
        "teams": {
            "backend_team": {
                "description": "handles backend development database api server logic",
                "competencies": ["python", "fastapi", "database"]
            },
            "frontend_team": {
                "description": "handles frontend development ui components javascript react",
                "competencies": ["javascript", "react", "css"]
            },
            "security_team": {
                "description": "handles security authentication authorization encryption",
                "competencies": ["security", "cryptography", "owasp"]
            },
            "operations_team": {
                "description": "handles deployment monitoring scaling infrastructure",
                "competencies": ["docker", "kubernetes", "monitoring"]
            },
            "testing_team": {
                "description": "handles testing quality assurance automation",
                "competencies": ["pytest", "selenium", "coverage"]
            }
        }
    }


@pytest.fixture
def benchmark_prompts():
    """Various prompt lengths for benchmarking."""
    return [
        "I need to implement user authentication",
        "How do I optimize database queries for better performance?",
        "I want to add a new feature to the frontend with React components",
        "The application needs better error handling and logging",
        "We should implement automated testing for the API endpoints",
        "Security vulnerability found in the authentication system that needs immediate attention",
        "The database is running slow and we need to optimize the queries and indexes",
        "Frontend performance is degraded and we need to implement code splitting and lazy loading",
        "Monitoring and alerting system needs to be enhanced for production deployment",
        "CI/CD pipeline is failing and needs to be fixed with proper testing and deployment automation"
    ]


@pytest.mark.benchmark
def test_team_assignment_small_prompt(benchmark, sample_meta_prompt):
    """Benchmark team assignment with small prompt."""
    prompt = "I need database help"

    result = benchmark(auto_assign_teams, prompt, sample_meta_prompt)

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.benchmark
def test_team_assignment_medium_prompt(benchmark, sample_meta_prompt):
    """Benchmark team assignment with medium prompt."""
    prompt = "I need to implement user authentication with proper security measures"

    result = benchmark(auto_assign_teams, prompt, sample_meta_prompt)

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.benchmark
def test_team_assignment_large_prompt(benchmark, sample_meta_prompt):
    """Benchmark team assignment with large prompt."""
    prompt = """
    I need to implement a comprehensive user management system that includes
    authentication, authorization, profile management, and role-based access control.
    The system should handle password hashing, JWT tokens, email verification,
    password reset functionality, and proper error handling throughout.
    """

    result = benchmark(auto_assign_teams, prompt, sample_meta_prompt)

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.benchmark
def test_team_assignment_multiple_teams(benchmark, benchmark_prompts):
    """Benchmark team assignment across multiple prompts."""
    meta_prompt = {
        "teams": {
            "backend_team": {
                "description": "backend database api server development",
                "competencies": ["python", "sql", "api"]
            },
            "frontend_team": {
                "description": "frontend ui javascript react development",
                "competencies": ["javascript", "react", "ui"]
            }
        }
    }

    def run_multiple_assignments():
        results = []
        for prompt in benchmark_prompts:
            result = auto_assign_teams(prompt, meta_prompt)
            results.append(result)
        return results

    results = benchmark(run_multiple_assignments)

    assert isinstance(results, list)
    assert len(results) == len(benchmark_prompts)
    assert all(isinstance(r, list) for r in results)


@pytest.mark.benchmark
def test_team_assignment_empty_teams(benchmark):
    """Benchmark team assignment with no teams defined (fallback case)."""
    prompt = "I need help with something"
    meta_prompt = {"teams": {}}

    result = benchmark(auto_assign_teams, prompt, meta_prompt)

    assert isinstance(result, list)
    assert len(result) >= 1  # Should return fallback teams


@pytest.mark.benchmark
def test_team_assignment_complex_meta_prompt(benchmark):
    """Benchmark with complex meta prompt structure."""
    # Create a more complex meta prompt with nested structures
    meta_prompt = {
        "teams": {
            team_name: {
                "description": f"handles {team_name} related tasks and functionality",
                "competencies": [f"{team_name}_skill_{i}" for i in range(5)],
                "metadata": {
                    "priority": i,
                    "complexity": "high" if i % 2 == 0 else "medium"
                }
            }
            for i, team_name in enumerate([
                "authentication", "database", "frontend", "backend",
                "security", "testing", "deployment", "monitoring"
            ])
        }
    }

    prompt = "I need to implement secure user authentication with database integration"

    result = benchmark(auto_assign_teams, prompt, meta_prompt)

    assert isinstance(result, list)
    assert len(result) > 0
