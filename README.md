# Leave Management System (SLMS)


## 📌 Overview

A scalable backend system for managing employee leave requests, approvals, and tracking.

This project simulates a real-world enterprise leave management workflow with modular architecture and clean separation of concerns.

---

## 🚀 Features

* Apply for leave
* Admin approval workflow
* Rule-based leave validation
* Audit logging system
* Modular service-based backend

---

## 🧱 System Design

Detailed system design is available in:

```
system-design/
```

Includes:

* Architecture diagram
* Workflow design

---

## ⚙️ Tech Stack

* **Backend:** FastAPI
* **Database:** PostgreSQL
* **Architecture:** Service-layer based

---

## 📂 Project Structure

```
app/
 ├── core/          # configs, auth, dependencies
 ├── db/            # database and migrations
 ├── models/        # schemas
 ├── routers/       # API routes
 ├── services/      # business logic
 ├── worker/        # background jobs
```

---

## 🔑 Key Highlights

* Clean architecture (separation of concerns)
* Scalable backend design
* Service layer abstraction
* Production-like API structure

---

## 📌 Future Improvements

* JWT Authentication
* Role-Based Access Control (RBAC)
* Email notifications
* Distributed task queue

---

## 🧠 Learning Outcome

This project demonstrates backend engineering fundamentals including API design, database handling, and scalable system architecture.
