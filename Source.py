from mesa import Agent, Model
from mesa.time import RandomActivation
import random
from rdflib import Graph, Namespace

# Load and parse the ontology
ontology_file = "healthcareonto.rdf"  # Ensure this is the path to your RDF file
ontology = Graph()
try:
    ontology.parse(ontology_file, format="xml")
except Exception as e:
    print(f"Error loading ontology file: {e}")
    exit(1)  # Exit if the ontology can't be loaded

# Define namespace (modify as per your ontology)
HEALTH = Namespace("http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15/")

class PatientAgent(Agent):
    """Represents a patient with a disease."""
    def __init__(self, unique_id, model, disease):
        super().__init__(unique_id, model)
        self.disease = disease
        self.treatment = None  # Initialize treatment
        self.doctor = None     # Initialize doctor
        self.nurse = None      # Initialize nurse
        self.ward = None       # Initialize ward

    def assign_treatment(self):
        """Retrieve treatment for the patient's disease from the ontology."""
        print(f"Searching for treatment for disease: {self.disease}")
        try:
            treatment_query = f"""
            SELECT ?treatment
            WHERE {{
                ?disease <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#hasTreatment> ?treatment .
                FILTER (?disease = <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#{self.disease}>)
            }}
            """
            treatment_results = list(ontology.query(treatment_query))
            if treatment_results:
                self.treatment = str(treatment_results[0][0].split("#")[-1])
            else:
                self.treatment = "No treatment found in ontology"
        except Exception as e:
            print(f"Error retrieving treatment for patient {self.unique_id}: {e}")

    def assign_doctor(self):
        """Assign a doctor to the patient based on the ontology."""
        try:
            doctor_query = f"""
            SELECT ?doctor
            WHERE {{
                ?treatment rdf:type <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#Treatment> .
                ?treatment <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#assignto> ?doctor .
                FILTER (?treatment = <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#{self.treatment}>)
            }}
            """
            doctor_results = list(ontology.query(doctor_query))
            if doctor_results:
                self.doctor = str(doctor_results[0][0].split("#")[-1])
            else:
                self.doctor = "No doctor found in ontology"
        except Exception as e:
            print(f"Error retrieving doctor for patient {self.unique_id}: {e}")

    def assign_nurse(self):
        """Assign a nurse to the patient based on the ontology."""
        try:
            nurse_query = f"""
            SELECT ?nurse
            WHERE {{
                ?nurse rdf:type <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#Nurse> .
                ?doctor<http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#hasNurse> ?nurse . 
                FILTER (?doctor = <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#{self.doctor}>)
            }}
            """
            nurse_results = list(ontology.query(nurse_query))
            if nurse_results:
                self.nurse = str(nurse_results[0][0].split("#")[-1])
            else:
                self.nurse = "No nurse found in ontology"
        except Exception as e:
           (f"Error retrieving nurse for patient {self.unique_id}: {e}")

    def assign_ward(self):
        """Assign a ward to the patient based on the ontology."""
        try:
            ward_query = f"""
            SELECT ?ward
            WHERE {{
                ?disease <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#hasward> ?ward .
                FILTER (?disease = <http://www.semanticweb.org/hansa/ontologies/2024/11/untitled-ontology-15#{self.disease}>)
            }}
            """
            ward_results = list(ontology.query(ward_query))
            if ward_results:
                self.ward = str(ward_results[0][0].split("#")[-1])
            else:
                self.ward = "No ward found in ontology"
        except Exception as e:
            print(f"Error retrieving ward for patient {self.unique_id}: {e}")

    def step(self):
        """Simulate the patient's step in the environment."""
        try:
            self.assign_treatment()
            self.assign_doctor()
            self.assign_nurse()
            self.assign_ward()
            print(f"Patient {self.unique_id} treated for {self.disease}:")
            print(f"  - Treatment: {self.treatment}")
            print(f"  - Doctor: {self.doctor}")
            print(f"  - Nurse: {self.nurse}")
            print(f"  - Ward: {self.ward}")
        except Exception as e:
            print(f"Error in step for patient {self.unique_id}: {e}")


class DoctorAgent(Agent):
    """Represents a doctor."""
    def __init__(self, unique_id, model, name):
        super().__init__(unique_id, model)
        self.name = name

    def assign_patient(self, patient):
        """Assign a patient to the doctor based on ontology."""
        patient.assign_doctor()


class NurseAgent(Agent):
    """Represents a nurse."""
    def __init__(self, unique_id, model, name):
        super().__init__(unique_id, model)
        self.name = name

    def assign_patient(self, patient):
        """Assign a nurse to the patient based on ontology."""
        patient.assign_nurse()


class WardAgent(Agent):
    """Represents a ward in the hospital."""
    def __init__(self, unique_id, model, name):
        super().__init__(unique_id, model)
        self.name = name

    def assign_patient(self, patient):
        """Assign a ward to the patient based on ontology."""
        patient.assign_ward()


class HealthcareModel(Model):
    """A healthcare model with patients, doctors, nurses, and wards."""
    def __init__(self, num_doctors, num_nurses, num_wards):
        self.schedule = RandomActivation(self)

        # Add doctors
        self.doctors = []
        for i in range(num_doctors):
            doctor = DoctorAgent(i, self, name=f"Doctor {i}")
            self.schedule.add(doctor)
            self.doctors.append(doctor)

        # Add nurses
        self.nurses = []
        for i in range(num_nurses):
            nurse = NurseAgent(i + num_doctors, self, name=f"Nurse {i}")
            self.schedule.add(nurse)
            self.nurses.append(nurse)

        # Add wards
        self.wards = []
        for i in range(num_wards):
            ward = WardAgent(i + num_doctors + num_nurses, self, name=f"Ward {i}")
            self.schedule.add(ward)
            self.wards.append(ward)

        self.patient_counter = num_doctors + num_nurses + num_wards

    def step(self):
        """Advance the model by one step."""
        disease = random.choice(["Disease1", "Disease2", "Disease3", "Disease4"])
        patient = PatientAgent(self.patient_counter, self, disease)
        self.patient_counter += 1
        self.schedule.add(patient)

        # Assign doctors, nurses, and wards
        doctor = random.choice(self.doctors)
        nurse = random.choice(self.nurses)
        ward = random.choice(self.wards)

        # Assign each agent (doctor, nurse, ward) to the patient
        doctor.assign_patient(patient)
        nurse.assign_patient(patient)
        ward.assign_patient(patient)

        print(f"\nNew Patient {patient.unique_id} arrives with disease: {disease}")
        self.schedule.step()

# Running the model
model = HealthcareModel(num_doctors=3, num_nurses=2, num_wards=2)
for i in range(3):  # Run for 3 steps
    print(f"\n=== Step {i + 1} ===")
    model.step()
