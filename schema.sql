/* ================================================================
   ENUM TYPES
   ================================================================ */
CREATE TYPE admin_role AS ENUM (
    'faculty_admin',
    'faculty_head',
    'department_manager',
    'general_admin',
    'super_admin'
);

CREATE TYPE general_status AS ENUM ('pending','approved','rejected');
CREATE TYPE event_type     AS ENUM ('faculty', 'university', 'global');
CREATE TYPE actor_type     AS ENUM ('admin');                 -- extensible
CREATE TYPE target_type    AS ENUM ('event', 'solidarity','family');
CREATE TYPE owner_type     AS ENUM ('student','event','solidarity','family');
CREATE TYPE housing_status AS ENUM ('rent', 'owned');

/* ================================================================
   CORE TABLES
   ================================================================ */

/* ---------- faculties ---------- */
CREATE TABLE faculties (
    faculty_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    major       VARCHAR(255) NOT NULL,
    created_at  timestamptz  NOT NULL DEFAULT now()
);

/* ---------- departments (youth-welfare) ---------- */
CREATE TABLE departments (
    dept_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  timestamptz NOT NULL DEFAULT now()
);

/* ---------- admins ---------- */
CREATE TABLE admins (
    admin_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password    BYTEA        NOT NULL,                 -- salted hash
    role        admin_role   NOT NULL,
    faculty_id  INTEGER,                               -- FK added later
    dept_id     INTEGER,                               -- FK added later
    created_at  timestamptz DEFAULT now(),
    can_create  BOOLEAN DEFAULT FALSE,
    can_update  BOOLEAN DEFAULT FALSE,
    can_read    BOOLEAN DEFAULT TRUE,
    can_delete  BOOLEAN DEFAULT FALSE,
    acc_status  VARCHAR(20) DEFAULT 'active'
);

/* ---------- students ---------- */
CREATE TABLE students (
    student_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password      BYTEA        NOT NULL,
    faculty_id    INTEGER NOT NULL,                    -- FK added later
    profile_photo VARCHAR(255),
    gender        CHAR(1)     NOT NULL,
    nid           TEXT        NOT NULL UNIQUE,
    uid           TEXT        NOT NULL UNIQUE,
    phone_number  TEXT        NOT NULL UNIQUE
                  CHECK (phone_number ~ '^\+?[0-9]{6,15}$'),
    address       VARCHAR(255) NOT NULL,
    acd_year      VARCHAR(50)  NOT NULL,
    join_date     DATE         NOT NULL,
    gpa           DECIMAL(4,2),
    grade         VARCHAR(50),
    major         VARCHAR(255) NOT NULL
);

/* ---------- events ---------- */
CREATE TABLE events (
    event_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title        VARCHAR(150) NOT NULL,
    description  TEXT,
    dept_id      INTEGER,                       -- FK added later
    faculty_id   INTEGER,                       -- FK added later
    created_by   INTEGER  NOT NULL,                       -- FK added later (admin)
    updated_at timestamptz DEFAULT now(),
    type         event_type,
    cost         DECIMAL(10,2),
    location     VARCHAR(150),
    restrictions TEXT,
    reward       TEXT,
    status       general_status DEFAULT 'pending',
    imgs         VARCHAR(255),
    st_date      DATE NOT NULL,
    end_date     DATE NOT NULL,
    s_limit      INTEGER,
    created_at   timestamptz DEFAULT now(),
    CHECK (end_date >= st_date)
);

/* ---------- families ---------- */
CREATE TABLE families (
    family_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    description  TEXT,
    faculty_id   INTEGER,                       -- FK added later
    created_by   INTEGER,                       -- FK added later (admin)
    approved_by  INTEGER,                       -- FK added later (admin)
    status       general_status DEFAULT 'pending',
    created_at   timestamptz DEFAULT now(),
    updated_at   timestamptz DEFAULT now()
);

CREATE TABLE family_members (
    family_id   INTEGER NOT NULL,
    student_id  INTEGER NOT NULL,
    role        VARCHAR(30) DEFAULT 'member',
    status      general_status DEFAULT 'pending',
    joined_at   timestamptz DEFAULT now(),
    PRIMARY KEY (family_id, student_id)
);

/* ---------- solidarities ---------- */
CREATE TABLE solidarities (
    solidarity_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id        INTEGER,                    -- FK added later
    faculty_id        INTEGER,                    -- FK added later
    req_status        general_status DEFAULT 'pending',
    created_at        timestamptz DEFAULT now(),
    family_numbers    INTEGER NOT NULL,
    father_status     VARCHAR(50),
    mother_status     VARCHAR(50),
    father_income     DECIMAL(10,2),
    mother_income     DECIMAL(10,2),
    total_income      DECIMAL(10,2),
    arrange_of_brothers INTEGER,
    m_phone_num       TEXT CHECK (m_phone_num IS NULL OR m_phone_num ~ '^\+?[0-9]{6,15}$'),
    f_phone_num       TEXT CHECK (f_phone_num IS NULL OR f_phone_num ~ '^\+?[0-9]{6,15}$'),
    reason            TEXT NOT NULL,
    docs              VARCHAR(255),
    disabilities      TEXT,
    housing_status    housing_status,
    grade             VARCHAR(50),
    acd_status        VARCHAR(50),
    address           VARCHAR(255) NOT NULL,
    approved_by       INTEGER  ,            -- FK added later
    updated_at timestamptz DEFAULT now()
);

/* ---------- prtcps (event-student junction) ---------- */
CREATE TABLE prtcps (
    event_id    INTEGER NOT NULL,
    student_id  INTEGER NOT NULL,
    rank        INTEGER,
    reward      VARCHAR(255),
    status      general_status DEFAULT 'pending',
    PRIMARY KEY (event_id, student_id)
);
--COMMENT ON COLUMN prtcps.status IS '(approved , rejected)';

/* ---------- documents ---------- */
CREATE TABLE documents (
    doc_id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_type  owner_type,
    owner_id    INTEGER NOT NULL,
    f_name      VARCHAR(255) NOT NULL,
    f_path      VARCHAR(255) NOT NULL,
    f_type      VARCHAR(50)  NOT NULL,
    uploaded_at timestamptz DEFAULT now()
);

/* ---------- logs ---------- */
CREATE TABLE logs (
    log_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id      INTEGER NOT NULL,                 -- FK to admins only
    actor_type    actor_type DEFAULT 'admin',
    action        VARCHAR(100) NOT NULL,
    target_type   target_type NOT NULL,
    event_id      INTEGER,                          -- nullable FK
    solidarity_id INTEGER,                          -- nullable FK
    family_id     INTEGER,                          -- nullable FK to families
    ip_address    INET,
    logged_at     timestamptz DEFAULT now()
);

/* ================================================================
   FOREIGN-KEY CONSTRAINTS
   ================================================================ */

/* admins → faculties / departments */
ALTER TABLE admins
    ADD CONSTRAINT admins_faculty_fk
    FOREIGN KEY (faculty_id)
    REFERENCES faculties(faculty_id)
    ON DELETE SET NULL;

ALTER TABLE admins
    ADD CONSTRAINT admins_dept_fk
    FOREIGN KEY (dept_id)
    REFERENCES departments(dept_id)
    ON DELETE SET NULL;

/* students → faculties */
ALTER TABLE students
    ADD CONSTRAINT students_faculty_fk
    FOREIGN KEY (faculty_id)
    REFERENCES faculties(faculty_id)
    ON DELETE CASCADE;

/* events foreign keys */
ALTER TABLE events
    ADD CONSTRAINT events_dept_fk
    FOREIGN KEY (dept_id)
    REFERENCES departments(dept_id)
    ON DELETE SET NULL;

ALTER TABLE events
    ADD CONSTRAINT events_faculty_fk
    FOREIGN KEY (faculty_id)
    REFERENCES faculties(faculty_id)
    ON DELETE SET NULL;

ALTER TABLE events
    ADD CONSTRAINT events_created_by_fk
    FOREIGN KEY (created_by)
    REFERENCES admins(admin_id)
    ON DELETE SET NULL;

/* families foreign keys */
ALTER TABLE families
    ADD CONSTRAINT families_faculty_fk
    FOREIGN KEY (faculty_id)
    REFERENCES faculties(faculty_id)
    ON DELETE SET NULL;

ALTER TABLE families
    ADD CONSTRAINT families_created_by_fk
    FOREIGN KEY (created_by)
    REFERENCES admins(admin_id)
    ON DELETE SET NULL;

ALTER TABLE families
    ADD CONSTRAINT families_approved_by_fk
    FOREIGN KEY (approved_by)
    REFERENCES admins(admin_id)
    ON DELETE SET NULL;

/* family_members junction */
ALTER TABLE family_members
    ADD CONSTRAINT family_members_family_fk
    FOREIGN KEY (family_id)
    REFERENCES families(family_id)
    ON DELETE CASCADE;

ALTER TABLE family_members
    ADD CONSTRAINT family_members_student_fk
    FOREIGN KEY (student_id)
    REFERENCES students(student_id)
    ON DELETE CASCADE;

/* solidarities foreign keys */
ALTER TABLE solidarities
    ADD CONSTRAINT solidarities_student_fk
    FOREIGN KEY (student_id)
    REFERENCES students(student_id)
    ON DELETE SET NULL;

ALTER TABLE solidarities
    ADD CONSTRAINT solidarities_faculty_fk
    FOREIGN KEY (faculty_id)
    REFERENCES faculties(faculty_id)
    ON DELETE SET NULL;

ALTER TABLE solidarities
    ADD CONSTRAINT solidarities_approved_by_fk
    FOREIGN KEY (approved_by)
    REFERENCES admins(admin_id)
    ON DELETE SET NULL;

/* prtcps junction */
ALTER TABLE prtcps
    ADD CONSTRAINT prtcps_event_fk
    FOREIGN KEY (event_id)
    REFERENCES events(event_id)
    ON DELETE CASCADE;

ALTER TABLE prtcps
    ADD CONSTRAINT prtcps_student_fk
    FOREIGN KEY (student_id)
    REFERENCES students(student_id)
    ON DELETE CASCADE;

/* logs foreign keys */
ALTER TABLE logs
    ADD CONSTRAINT logs_actor_fk
    FOREIGN KEY (actor_id)
    REFERENCES admins(admin_id)
    ON DELETE SET NULL;

ALTER TABLE logs
    ADD CONSTRAINT logs_event_fk
    FOREIGN KEY (event_id)
    REFERENCES events(event_id)
    ON DELETE SET NULL;

ALTER TABLE logs
    ADD CONSTRAINT logs_solidarity_fk
    FOREIGN KEY (solidarity_id)
    REFERENCES solidarities(solidarity_id)
    ON DELETE SET NULL;

ALTER TABLE logs
    ADD CONSTRAINT logs_family_fk
    FOREIGN KEY (family_id)
    REFERENCES families(family_id)
    ON DELETE SET NULL;

ALTER TABLE logs
ADD CONSTRAINT logs_single_target_check
CHECK (
    (target_type = 'event' AND event_id IS NOT NULL AND solidarity_id IS NULL AND family_id IS NULL) OR
    (target_type = 'solidarity' AND solidarity_id IS NOT NULL AND event_id IS NULL AND family_id IS NULL) OR
    (target_type = 'family' AND family_id IS NOT NULL AND event_id IS NULL AND solidarity_id IS NULL)
);
/* ================================================================
   ROLE-SPECIFIC CONSTRAINTS
   ================================================================ */

/* 1. every faculty can have at most ONE faculty_head */
CREATE UNIQUE INDEX one_head_per_faculty
       ON admins (faculty_id)
       WHERE role = 'faculty_head';

/* 2. roles that must belong to a faculty */
ALTER TABLE admins
ADD CONSTRAINT role_needs_faculty_chk
CHECK (
    (role IN ('faculty_head','faculty_admin') AND faculty_id IS NOT NULL)
    OR
    (role NOT IN ('faculty_head','faculty_admin'))
);

/* 3. roles that must belong to a department */
ALTER TABLE admins
ADD CONSTRAINT role_needs_dept_chk
CHECK (
    (role = 'department_manager' AND dept_id IS NOT NULL)
    OR
    (role <> 'department_manager')
);

/* ================================================================
   INDEXES FOR FOREIGN-KEY COLUMNS
   ================================================================ */
CREATE INDEX idx_admins_faculty_id         ON admins   (faculty_id);
CREATE INDEX idx_admins_dept_id            ON admins   (dept_id);
CREATE INDEX idx_students_faculty_id       ON students (faculty_id);
CREATE INDEX idx_events_dept_id            ON events   (dept_id);
CREATE INDEX idx_events_faculty_id         ON events   (faculty_id);
CREATE INDEX idx_events_created_by         ON events   (created_by);
CREATE INDEX idx_families_faculty_id       ON families (faculty_id);
CREATE INDEX idx_family_members_student    ON family_members (student_id);
CREATE INDEX idx_solidarities_student      ON solidarities (student_id);
CREATE INDEX idx_solidarities_faculty      ON solidarities (faculty_id);
CREATE INDEX idx_prtcps_student            ON prtcps (student_id);
CREATE INDEX idx_families_created_by       ON families(created_by);
/* logs indexes */
CREATE INDEX idx_logs_actor_id      ON logs (actor_id);
CREATE INDEX idx_logs_target        ON logs (target_type, event_id, solidarity_id, family_id);
CREATE INDEX idx_logs_logged_at     ON logs (logged_at);
CREATE INDEX idx_logs_action        ON logs (action);

/* ================================================================
   UPDATED_AT TRIGGER
   ================================================================ */
-- generic function (we already created it for families, re-use it)
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- attach to every table that owns updated_at
CREATE TRIGGER trg_families_touch
BEFORE UPDATE ON families
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_events_touch
BEFORE UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_solidarities_touch
BEFORE UPDATE ON solidarities
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-------------------------------------------------------------------
/* ================================================================
   2.  Audit log – INSERT row after important actions
   ================================================================ */
-------------------------------------------------------------------
/* Helper to capture the client IP address */
CREATE OR REPLACE FUNCTION client_ip() RETURNS inet
LANGUAGE SQL STABLE AS
$$ SELECT COALESCE(inet_client_addr(), '0.0.0.0') $$;

-------------------------------------------------------------------
--2-A  WHEN AN ADMIN CREATES A NEW EVENT
-------------------------------------------------------------------
CREATE OR REPLACE FUNCTION log_event_insert()
RETURNS trigger AS $$
BEGIN
    INSERT INTO logs (actor_id,
                      action,
                      target_type,
                      event_id,
                      ip_address)
    VALUES (NEW.created_by,
            'create_event',
            'event',
            NEW.event_id,
            client_ip());

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_event_insert
AFTER INSERT ON events
FOR EACH ROW EXECUTE FUNCTION log_event_insert();

-------------------------------------------------------------------
--2-B  WHEN AN ADMIN APPROVES A SOLIDARITY REQUEST
-------------------------------------------------------------------
/*  – fires only when approved_by is set for the first time
    – or when req_status changes from anything ≠ 'approved' to 'approved'
*/
CREATE OR REPLACE FUNCTION log_solidarity_approval()
RETURNS trigger AS $$
BEGIN
    INSERT INTO logs (actor_id,
                      action,
                      target_type,
                      solidarity_id,
                      ip_address)
    VALUES (NEW.approved_by,
            'approve_solidarity',
            'solidarity',
            NEW.solidarity_id,
            client_ip());

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


--
DROP TRIGGER trg_log_solidarity_approval ON solidarities

CREATE TRIGGER trg_log_solidarity_approval
AFTER UPDATE ON solidarities
FOR EACH ROW
WHEN (

      (OLD.req_status  IS DISTINCT FROM NEW.req_status
         AND NEW.req_status = 'approved')
     )
EXECUTE FUNCTION log_solidarity_approval();

-- 3-B WHEN AN ADMIN REJECTS A SOLIDARITY REQUEST
---------------------------------------------------------------
CREATE OR REPLACE FUNCTION log_solidarity_rejection()
RETURNS trigger AS $$
BEGIN
    INSERT INTO logs (actor_id,
                      action,
                      target_type,
                      solidarity_id,
                      ip_address)
    VALUES (NEW.approved_by,  
            'reject_solidarity',
            'solidarity',
            NEW.solidarity_id,
            client_ip());

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_log_solidarity_rejection
AFTER UPDATE ON solidarities
FOR EACH ROW
WHEN (
        OLD.req_status IS DISTINCT FROM NEW.req_status
        AND NEW.req_status = 'rejected'
     )
EXECUTE FUNCTION log_solidarity_rejection();



