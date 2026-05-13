from crewai import Agent, Crew, Process, Task
from crewai.memory.unified_memory import Memory
from crewai.memory.storage.lancedb_storage import LanceDBStorage
from crewai.project import CrewBase, agent, crew, task

from healthcare_app.tools.custom_tool import MedicalRAGTool
from healthcare_app.tools.serper_tool import SerperMedicalSearchTool


@CrewBase
class HealthcareAssistance():
    """Healthcare Assistance crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ── Agents ────────────────────────────────────────────────────────────

    @agent
    def manager(self) -> Agent:
        return Agent(
            config=self.agents_config['manager'],
            verbose=True,
        )

    @agent
    def medical_records_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['medical_records_manager'],
            verbose=True,
            tools=[MedicalRAGTool()],
        )

    @agent
    def healthcare_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config['healthcare_assistant'],
            verbose=True,
        )

    @agent
    def medical_research_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['medical_research_specialist'],
            verbose=True,
            tools=[MedicalRAGTool(), SerperMedicalSearchTool()],
        )

    # ── Tasks ─────────────────────────────────────────────────────────────

    @task
    def identify_intent(self) -> Task:
        return Task(config=self.tasks_config['identify_intent'])

    @task
    def retrieve_medical_history(self) -> Task:
        return Task(config=self.tasks_config['retrieve_medical_history'])

    @task
    def book_appointment(self) -> Task:
        return Task(config=self.tasks_config['book_appointment'])

    @task
    def research_ckd_treatment(self) -> Task:
        return Task(config=self.tasks_config['research_ckd_treatment'])

    # ── Crew ──────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the Healthcare Assistance crew"""

        # crewai 1.14.4 uses a unified Memory class (LanceDB-backed vector store)
        # that handles long-term persistence, semantic retrieval, and entity
        # tracking in a single store — replacing the old LongTermMemory /
        # ShortTermMemory / EntityMemory split.
        healthcare_memory = Memory(
            # Persist the vector DB under memory/ so patient records, CKD
            # diagnoses, and booking history survive across sessions.
            storage=LanceDBStorage(
                path="./memory/healthcare_lancedb",
                table_name="healthcare_memories",
            ),
            # text-embedding-3-small: cost-efficient, accurate for clinical
            # terminology, and consistent with the RAG pipeline embedder.
            embedder={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                },
            },
            # Tune weights for healthcare: semantic relevance matters most;
            # recency is less critical because a CKD diagnosis from last week
            # is as valid as one from an hour ago.
            semantic_weight=0.6,
            recency_weight=0.2,
            importance_weight=0.2,
            # Medical records stay relevant much longer than general chat —
            # 90-day half-life prevents premature decay of patient history.
            recency_half_life_days=90,
            # Treat all stored medical facts as high-importance by default.
            default_importance=0.7,
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=healthcare_memory,
            verbose=True,
        )

