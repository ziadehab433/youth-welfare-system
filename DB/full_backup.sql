--
-- PostgreSQL database dump
--

\restrict P5EnfxzXpcYUdWOz3a8epJmeMwu9TZAXKGV7GpFxe2C0dng9FurSHMIXWeGLIHU

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: actor_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.actor_type AS ENUM (
    'مسؤول كلية',
    'مدير كلية',
    'مدير إدارة',
    'مدير عام',
    'مشرف النظام',
    'طالب'
);


ALTER TYPE public.actor_type OWNER TO postgres;

--
-- Name: admin_role; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.admin_role AS ENUM (
    'مسؤول كلية',
    'مدير كلية',
    'مدير ادارة',
    'مدير عام',
    'مشرف النظام'
);


ALTER TYPE public.admin_role OWNER TO postgres;

--
-- Name: event_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.event_type AS ENUM (
    'داخلي',
    'خارجي',
    'اخر'
);


ALTER TYPE public.event_type OWNER TO postgres;

--
-- Name: general_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.general_status AS ENUM (
    'موافقة مبدئية',
    'مقبول',
    'منتظر',
    'مرفوض'
);


ALTER TYPE public.general_status OWNER TO postgres;

--
-- Name: housing_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.housing_status AS ENUM (
    'ايجار',
    'ملك'
);


ALTER TYPE public.housing_status OWNER TO postgres;

--
-- Name: owner_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.owner_type AS ENUM (
    'نشاط',
    'طالب',
    'تكافل',
    'اسر'
);


ALTER TYPE public.owner_type OWNER TO postgres;

--
-- Name: req_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.req_type_enum AS ENUM (
    'مصاريف كتب',
    'مصاريف انتساب',
    'مصاريف انتظام',
    'مصاريف كاملة',
    'اخرى'
);


ALTER TYPE public.req_type_enum OWNER TO postgres;

--
-- Name: sol_doc_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.sol_doc_type AS ENUM (
    'بحث احتماعي',
    'اثبات دخل',
    'ص.ب ولي امر',
    'ص.ب شخصية',
    'حبازة زراعية'
);


ALTER TYPE public.sol_doc_type OWNER TO postgres;

--
-- Name: target_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.target_type AS ENUM (
    'نشاط',
    'تكافل',
    'اسر',
    'اخر'
);


ALTER TYPE public.target_type OWNER TO postgres;

--
-- Name: client_ip(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.client_ip() RETURNS inet
    LANGUAGE sql STABLE
    AS $$ SELECT COALESCE(inet_client_addr(), '0.0.0.0') $$;


ALTER FUNCTION public.client_ip() OWNER TO postgres;

--
-- Name: log_event_insert(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_event_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO logs (actor_id,
                      action,
                      target_type,
                      event_id,
                      ip_address)
    VALUES (NEW.created_by,
            'انشاء نشاط',
            'نشاط',
            NEW.event_id,
            client_ip());
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_event_insert() OWNER TO postgres;

--
-- Name: log_family_insert(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_family_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO logs (actor_id, action, target_type, family_id, ip_address)
    VALUES (NEW.created_by, 'انشاء اسر', 'اسر', 
            NEW.family_id,    -- ← was NEW.event_id
            client_ip());
    RETURN NEW;
END;$$;


ALTER FUNCTION public.log_family_insert() OWNER TO postgres;

--
-- Name: log_solidarity_approval(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_solidarity_approval() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO logs (actor_id,
                      action,
                      target_type,
                      solidarity_id,
                      ip_address)
    VALUES (NEW.approved_by,
            'موافقة طلب',
            'تكافل',
            NEW.solidarity_id,
            client_ip());
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_solidarity_approval() OWNER TO postgres;

--
-- Name: log_solidarity_rejection(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_solidarity_rejection() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO logs (actor_id,
                      action,
                      target_type,
                      solidarity_id,
                      ip_address)
    VALUES (NEW.approved_by,  
            'رفض طلب',
            'تكافل',
            NEW.solidarity_id,
            client_ip());
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_solidarity_rejection() OWNER TO postgres;

--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_updated_at() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admins (
    admin_id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    password bytea NOT NULL,
    faculty_id integer,
    dept_id integer,
    created_at timestamp with time zone DEFAULT now(),
    can_create boolean DEFAULT false,
    can_update boolean DEFAULT false,
    can_read boolean DEFAULT true,
    can_delete boolean DEFAULT false,
    acc_status character varying(20) DEFAULT 'active'::character varying,
    role public.admin_role
);


ALTER TABLE public.admins OWNER TO postgres;

--
-- Name: admins_admin_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.admins ALTER COLUMN admin_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.admins_admin_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO postgres;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO postgres;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO postgres;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: departments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.departments (
    dept_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.departments OWNER TO postgres;

--
-- Name: departments_dept_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.departments ALTER COLUMN dept_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.departments_dept_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    doc_id integer NOT NULL,
    owner_id integer NOT NULL,
    f_name character varying(255) NOT NULL,
    f_path character varying(255) NOT NULL,
    f_type character varying(50) NOT NULL,
    uploaded_at timestamp with time zone DEFAULT now(),
    owner_type public.owner_type
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- Name: documents_doc_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.documents ALTER COLUMN doc_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.documents_doc_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: event_docs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_docs (
    doc_id integer NOT NULL,
    event_id integer NOT NULL,
    doc_type character varying(40) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_path character varying(255) NOT NULL,
    mime_type character varying(80),
    file_size integer,
    uploaded_at timestamp with time zone DEFAULT now(),
    uploaded_by integer
);


ALTER TABLE public.event_docs OWNER TO postgres;

--
-- Name: event_docs_doc_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.event_docs_doc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.event_docs_doc_id_seq OWNER TO postgres;

--
-- Name: event_docs_doc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.event_docs_doc_id_seq OWNED BY public.event_docs.doc_id;


--
-- Name: events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.events (
    event_id integer NOT NULL,
    title character varying(150) NOT NULL,
    description text,
    dept_id integer,
    faculty_id integer,
    created_by integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    cost numeric(10,2),
    location character varying(150),
    restrictions text,
    reward text,
    status public.general_status DEFAULT 'منتظر'::public.general_status,
    imgs character varying(255),
    st_date date NOT NULL,
    end_date date NOT NULL,
    s_limit integer,
    created_at timestamp with time zone DEFAULT now(),
    type public.event_type,
    CONSTRAINT events_check CHECK ((end_date >= st_date))
);


ALTER TABLE public.events OWNER TO postgres;

--
-- Name: events_event_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.events ALTER COLUMN event_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.events_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: faculties; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.faculties (
    faculty_id integer NOT NULL,
    name character varying(100) NOT NULL,
    major character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.faculties OWNER TO postgres;

--
-- Name: faculties_faculty_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.faculties ALTER COLUMN faculty_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.faculties_faculty_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: families; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.families (
    family_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    faculty_id integer,
    created_by integer,
    approved_by integer,
    status public.general_status DEFAULT 'منتظر'::public.general_status,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.families OWNER TO postgres;

--
-- Name: families_family_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.families ALTER COLUMN family_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.families_family_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: family_members; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.family_members (
    family_id integer NOT NULL,
    student_id integer NOT NULL,
    role character varying(30) DEFAULT 'member'::character varying,
    status public.general_status DEFAULT 'منتظر'::public.general_status,
    joined_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.family_members OWNER TO postgres;

--
-- Name: logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.logs (
    log_id integer NOT NULL,
    actor_id integer NOT NULL,
    action character varying(100) NOT NULL,
    event_id integer,
    solidarity_id integer,
    family_id integer,
    ip_address inet,
    logged_at timestamp with time zone DEFAULT now(),
    actor_type public.actor_type,
    target_type public.target_type NOT NULL,
    CONSTRAINT logs_single_target_check CHECK ((((target_type = 'نشاط'::public.target_type) AND (event_id IS NOT NULL) AND (solidarity_id IS NULL) AND (family_id IS NULL)) OR ((target_type = 'تكافل'::public.target_type) AND (solidarity_id IS NOT NULL) AND (event_id IS NULL) AND (family_id IS NULL)) OR ((target_type = 'اسر'::public.target_type) AND (family_id IS NOT NULL) AND (event_id IS NULL) AND (solidarity_id IS NULL))))
);


ALTER TABLE public.logs OWNER TO postgres;

--
-- Name: logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.logs ALTER COLUMN log_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.logs_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: prtcps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prtcps (
    event_id integer NOT NULL,
    student_id integer NOT NULL,
    rank integer,
    reward character varying(255),
    status public.general_status DEFAULT 'منتظر'::public.general_status
);


ALTER TABLE public.prtcps OWNER TO postgres;

--
-- Name: solidarities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solidarities (
    solidarity_id integer NOT NULL,
    student_id integer,
    faculty_id integer,
    req_status public.general_status DEFAULT 'منتظر'::public.general_status,
    created_at timestamp with time zone DEFAULT now(),
    family_numbers integer NOT NULL,
    father_status character varying(50),
    mother_status character varying(50),
    father_income numeric(10,2),
    mother_income numeric(10,2),
    total_income numeric(10,2),
    arrange_of_brothers integer,
    m_phone_num text,
    f_phone_num text,
    reason text NOT NULL,
    disabilities text,
    grade character varying(50),
    acd_status character varying(50),
    address character varying(255) NOT NULL,
    approved_by integer,
    updated_at timestamp with time zone DEFAULT now(),
    req_type public.req_type_enum,
    housing_status public.housing_status,
    CONSTRAINT solidarities_f_phone_num_check CHECK (((f_phone_num IS NULL) OR (f_phone_num ~ '^\+?[0-9]{6,15}$'::text))),
    CONSTRAINT solidarities_m_phone_num_check CHECK (((m_phone_num IS NULL) OR (m_phone_num ~ '^\+?[0-9]{6,15}$'::text)))
);


ALTER TABLE public.solidarities OWNER TO postgres;

--
-- Name: solidarities_solidarity_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.solidarities ALTER COLUMN solidarity_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.solidarities_solidarity_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: solidarity_docs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solidarity_docs (
    doc_id integer NOT NULL,
    solidarity_id integer NOT NULL,
    doc_type public.sol_doc_type,
    file_name character varying(255) NOT NULL,
    file_path character varying(255) NOT NULL,
    mime_type character varying(80) NOT NULL,
    file_size integer,
    uploaded_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.solidarity_docs OWNER TO postgres;

--
-- Name: solidarity_docs_doc_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.solidarity_docs_doc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.solidarity_docs_doc_id_seq OWNER TO postgres;

--
-- Name: solidarity_docs_doc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.solidarity_docs_doc_id_seq OWNED BY public.solidarity_docs.doc_id;


--
-- Name: students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.students (
    student_id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    password bytea NOT NULL,
    faculty_id integer NOT NULL,
    profile_photo character varying(255),
    gender character(1) NOT NULL,
    nid text NOT NULL,
    uid text NOT NULL,
    phone_number text NOT NULL,
    address character varying(255) NOT NULL,
    acd_year character varying(50) NOT NULL,
    join_date date NOT NULL,
    gpa numeric(4,2),
    grade character varying(50),
    major character varying(255) NOT NULL,
    CONSTRAINT students_phone_number_check CHECK ((phone_number ~ '^\+?[0-9]{6,15}$'::text))
);


ALTER TABLE public.students OWNER TO postgres;

--
-- Name: students_student_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.students ALTER COLUMN student_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.students_student_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: event_docs doc_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_docs ALTER COLUMN doc_id SET DEFAULT nextval('public.event_docs_doc_id_seq'::regclass);


--
-- Name: solidarity_docs doc_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarity_docs ALTER COLUMN doc_id SET DEFAULT nextval('public.solidarity_docs_doc_id_seq'::regclass);


--
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admins (admin_id, name, email, password, faculty_id, dept_id, created_at, can_create, can_update, can_read, can_delete, acc_status, role) FROM stdin;
1	أحمد علي	ahmed@example.com	\\x736563726574	1	1	2025-10-20 02:34:30.31113+03	t	t	t	f	active	مدير كلية
2	سارة محمد	sara@example.com	\\x736563726574	2	\N	2025-10-20 02:34:30.31113+03	t	f	t	f	active	مسؤول كلية
3	أحمد علي	ahmed.faculty@example.com	\\x736563726574	1	\N	2025-10-20 02:53:23.217139+03	t	t	t	f	active	مسؤول كلية
4	سارة محمد	sara.head@example.com	\\x736563726574	1	1	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير كلية
5	خالد إبراهيم	khaled.manager@example.com	\\x736563726574	2	2	2025-10-20 02:53:23.217139+03	t	t	t	f	active	مدير ادارة
6	منى يوسف	mona.general@example.com	\\x736563726574	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير عام
7	محمد سعيد	mohamed.super@example.com	\\x736563726574	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مشرف النظام
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.departments (dept_id, name, description, created_at) FROM stdin;
1	نشاط فني و ثقافي	نشاط فني	2025-10-20 02:34:30.31113+03
2	نشاط رياضي	نشاط رياضي	2025-10-20 02:34:30.31113+03
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2025-10-11 20:19:28.802694+03
2	auth	0001_initial	2025-10-11 20:19:28.855341+03
3	admin	0001_initial	2025-10-11 20:19:28.872819+03
4	admin	0002_logentry_remove_auto_add	2025-10-11 20:19:28.877517+03
5	admin	0003_logentry_add_action_flag_choices	2025-10-11 20:19:28.882463+03
6	contenttypes	0002_remove_content_type_name	2025-10-11 20:19:28.892083+03
7	auth	0002_alter_permission_name_max_length	2025-10-11 20:19:28.897553+03
8	auth	0003_alter_user_email_max_length	2025-10-11 20:19:28.902847+03
9	auth	0004_alter_user_username_opts	2025-10-11 20:19:28.907245+03
10	auth	0005_alter_user_last_login_null	2025-10-11 20:19:28.913157+03
11	auth	0006_require_contenttypes_0002	2025-10-11 20:19:28.91415+03
12	auth	0007_alter_validators_add_error_messages	2025-10-11 20:19:28.918656+03
13	auth	0008_alter_user_username_max_length	2025-10-11 20:19:28.926498+03
14	auth	0009_alter_user_last_name_max_length	2025-10-11 20:19:28.931064+03
15	auth	0010_alter_group_name_max_length	2025-10-11 20:19:28.936314+03
16	auth	0011_update_proxy_permissions	2025-10-11 20:19:28.94082+03
17	auth	0012_alter_user_first_name_max_length	2025-10-11 20:19:28.945956+03
18	sessions	0001_initial	2025-10-11 20:19:28.95267+03
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.documents (doc_id, owner_id, f_name, f_path, f_type, uploaded_at, owner_type) FROM stdin;
\.


--
-- Data for Name: event_docs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.event_docs (doc_id, event_id, doc_type, file_name, file_path, mime_type, file_size, uploaded_at, uploaded_by) FROM stdin;
1	1	cover	cover.jpg	events/1/cover.jpg	image/jpeg	204800	2025-10-20 02:34:30.31113+03	1
2	1	agenda	agenda.pdf	events/1/agenda.pdf	application/pdf	102400	2025-10-20 02:34:30.31113+03	1
3	2	banner	banner.png	events/2/banner.png	image/png	300000	2025-10-20 02:34:30.31113+03	2
\.


--
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.events (event_id, title, description, dept_id, faculty_id, created_by, updated_at, cost, location, restrictions, reward, status, imgs, st_date, end_date, s_limit, created_at, type) FROM stdin;
1	معرض مشاريع التخرج	عرض مشاريع الطلاب	1	1	1	2025-10-20 02:34:30.31113+03	0.00	قاعة الاحتفالات	\N	\N	منتظر	\N	2025-12-01	2025-12-03	\N	2025-10-20 02:34:30.31113+03	داخلي
2	رحلة علمية	زيارة إلى مصنع الأدوية	\N	2	2	2025-10-20 02:34:30.31113+03	50.00	مصنع الحياة	\N	\N	منتظر	\N	2025-11-15	2025-11-15	\N	2025-10-20 02:34:30.31113+03	خارجي
\.


--
-- Data for Name: faculties; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.faculties (faculty_id, name, major, created_at) FROM stdin;
1	كلية الهندسة	هندسة عامة	2025-10-20 02:34:30.31113+03
2	كلية العلوم	علوم أساسية	2025-10-20 02:34:30.31113+03
\.


--
-- Data for Name: families; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.families (family_id, name, description, faculty_id, created_by, approved_by, status, created_at, updated_at) FROM stdin;
1	أسرة المبدعين	نشاط طلابي للابتكار	1	1	\N	منتظر	2025-10-20 02:34:30.31113+03	2025-10-20 02:34:30.31113+03
\.


--
-- Data for Name: family_members; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.family_members (family_id, student_id, role, status, joined_at) FROM stdin;
1	1	رئيس	منتظر	2025-10-20 02:34:30.31113+03
1	2	عضو	منتظر	2025-10-20 02:34:30.31113+03
\.


--
-- Data for Name: logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.logs (log_id, actor_id, action, event_id, solidarity_id, family_id, ip_address, logged_at, actor_type, target_type) FROM stdin;
1	1	انشاء نشاط	1	\N	\N	::1	2025-10-20 02:34:30.31113+03	\N	نشاط
2	2	انشاء نشاط	2	\N	\N	::1	2025-10-20 02:34:30.31113+03	\N	نشاط
3	1	انشاء اسر	\N	\N	1	::1	2025-10-20 02:34:30.31113+03	\N	اسر
\.


--
-- Data for Name: prtcps; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.prtcps (event_id, student_id, rank, reward, status) FROM stdin;
1	1	\N	\N	منتظر
1	2	\N	\N	منتظر
2	2	\N	\N	منتظر
\.


--
-- Data for Name: solidarities; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.solidarities (solidarity_id, student_id, faculty_id, req_status, created_at, family_numbers, father_status, mother_status, father_income, mother_income, total_income, arrange_of_brothers, m_phone_num, f_phone_num, reason, disabilities, grade, acd_status, address, approved_by, updated_at, req_type, housing_status) FROM stdin;
1	1	1	منتظر	2025-10-20 02:34:30.31113+03	6	موظف	ربة منزل	5000.00	0.00	5000.00	\N	\N	\N	مصاريف السكن	\N	\N	\N	الرياض	\N	2025-10-20 02:34:30.31113+03	\N	ايجار
\.


--
-- Data for Name: solidarity_docs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.solidarity_docs (doc_id, solidarity_id, doc_type, file_name, file_path, mime_type, file_size, uploaded_at) FROM stdin;
1	1	بحث احتماعي	research.pdf	solidarity/1/research.pdf	application/pdf	204800	2025-10-20 02:34:30.31113+03
2	1	اثبات دخل	income.pdf	solidarity/1/income.pdf	application/pdf	102400	2025-10-20 02:34:30.31113+03
3	1	ص.ب ولي امر	guardian.jpg	solidarity/1/guardian.jpg	image/jpeg	256000	2025-10-20 02:34:30.31113+03
4	1	ص.ب شخصية	id.jpg	solidarity/1/id.jpg	image/jpeg	180000	2025-10-20 02:34:30.31113+03
5	1	حبازة زراعية	farm.pdf	solidarity/1/farm.pdf	application/pdf	150000	2025-10-20 02:34:30.31113+03
\.


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.students (student_id, name, email, password, faculty_id, profile_photo, gender, nid, uid, phone_number, address, acd_year, join_date, gpa, grade, major) FROM stdin;
1	محمد سعيد	m.saeed@example.com	\\x736563726574	1	\N	M	123456789	987654321	+966501234567	الرياض	2025/2026	2025-09-01	\N	\N	هندسة حاسوب
2	ليلى خالد	l.khaled@example.com	\\x736563726574	2	\N	F	223456789	887654321	+966555555555	جدة	2025/2026	2025-09-01	\N	\N	كيمياء
\.


--
-- Name: admins_admin_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admins_admin_id_seq', 7, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 24, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, false);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: departments_dept_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.departments_dept_id_seq', 2, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 6, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 18, true);


--
-- Name: documents_doc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.documents_doc_id_seq', 2, true);


--
-- Name: event_docs_doc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.event_docs_doc_id_seq', 3, true);


--
-- Name: events_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.events_event_id_seq', 2, true);


--
-- Name: faculties_faculty_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.faculties_faculty_id_seq', 2, true);


--
-- Name: families_family_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.families_family_id_seq', 1, true);


--
-- Name: logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.logs_log_id_seq', 3, true);


--
-- Name: solidarities_solidarity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solidarities_solidarity_id_seq', 1, true);


--
-- Name: solidarity_docs_doc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solidarity_docs_doc_id_seq', 5, true);


--
-- Name: students_student_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.students_student_id_seq', 2, true);


--
-- Name: admins admins_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_email_key UNIQUE (email);


--
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (admin_id);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (dept_id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (doc_id);


--
-- Name: event_docs event_docs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_docs
    ADD CONSTRAINT event_docs_pkey PRIMARY KEY (doc_id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (event_id);


--
-- Name: faculties faculties_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faculties
    ADD CONSTRAINT faculties_pkey PRIMARY KEY (faculty_id);


--
-- Name: families families_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_pkey PRIMARY KEY (family_id);


--
-- Name: family_members family_members_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_pkey PRIMARY KEY (family_id, student_id);


--
-- Name: logs logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (log_id);


--
-- Name: prtcps prtcps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_pkey PRIMARY KEY (event_id, student_id);


--
-- Name: solidarities solidarities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_pkey PRIMARY KEY (solidarity_id);


--
-- Name: solidarity_docs solidarity_docs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarity_docs
    ADD CONSTRAINT solidarity_docs_pkey PRIMARY KEY (doc_id);


--
-- Name: solidarity_docs solidarity_docs_solidarity_id_doc_type_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarity_docs
    ADD CONSTRAINT solidarity_docs_solidarity_id_doc_type_key UNIQUE (solidarity_id, doc_type);


--
-- Name: students students_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_email_key UNIQUE (email);


--
-- Name: students students_nid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_nid_key UNIQUE (nid);


--
-- Name: students students_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_phone_number_key UNIQUE (phone_number);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (student_id);


--
-- Name: students students_uid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_uid_key UNIQUE (uid);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: idx_admins_dept_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_admins_dept_id ON public.admins USING btree (dept_id);


--
-- Name: idx_admins_faculty_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_admins_faculty_id ON public.admins USING btree (faculty_id);


--
-- Name: idx_event_docs_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_event_docs_event_id ON public.event_docs USING btree (event_id);


--
-- Name: idx_events_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_created_by ON public.events USING btree (created_by);


--
-- Name: idx_events_dept_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_dept_id ON public.events USING btree (dept_id);


--
-- Name: idx_events_faculty_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_faculty_id ON public.events USING btree (faculty_id);


--
-- Name: idx_families_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_families_created_by ON public.families USING btree (created_by);


--
-- Name: idx_families_faculty_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_families_faculty_id ON public.families USING btree (faculty_id);


--
-- Name: idx_family_members_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_family_members_student ON public.family_members USING btree (student_id);


--
-- Name: idx_logs_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_logs_action ON public.logs USING btree (action);


--
-- Name: idx_logs_actor_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_logs_actor_id ON public.logs USING btree (actor_id);


--
-- Name: idx_logs_logged_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_logs_logged_at ON public.logs USING btree (logged_at);


--
-- Name: idx_logs_target; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_logs_target ON public.logs USING btree (target_type, event_id, solidarity_id, family_id);


--
-- Name: idx_prtcps_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_prtcps_student ON public.prtcps USING btree (student_id);


--
-- Name: idx_solidarities_faculty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_solidarities_faculty ON public.solidarities USING btree (faculty_id);


--
-- Name: idx_solidarities_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_solidarities_student ON public.solidarities USING btree (student_id);


--
-- Name: idx_students_faculty_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_students_faculty_id ON public.students USING btree (faculty_id);


--
-- Name: events trg_events_touch; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_events_touch BEFORE UPDATE ON public.events FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: families trg_families_touch; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_families_touch BEFORE UPDATE ON public.families FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: events trg_log_event_insert; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_log_event_insert AFTER INSERT ON public.events FOR EACH ROW EXECUTE FUNCTION public.log_event_insert();


--
-- Name: families trg_log_family_insert; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_log_family_insert AFTER INSERT ON public.families FOR EACH ROW EXECUTE FUNCTION public.log_family_insert();


--
-- Name: solidarities trg_log_solidarity_approval; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_log_solidarity_approval AFTER UPDATE ON public.solidarities FOR EACH ROW WHEN (((old.req_status IS DISTINCT FROM new.req_status) AND (new.req_status = 'مقبول'::public.general_status))) EXECUTE FUNCTION public.log_solidarity_approval();


--
-- Name: solidarities trg_log_solidarity_rejection; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_log_solidarity_rejection AFTER UPDATE ON public.solidarities FOR EACH ROW WHEN (((old.req_status IS DISTINCT FROM new.req_status) AND (new.req_status = 'مرفوض'::public.general_status))) EXECUTE FUNCTION public.log_solidarity_rejection();


--
-- Name: solidarities trg_solidarities_touch; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_solidarities_touch BEFORE UPDATE ON public.solidarities FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: admins admins_dept_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_dept_fk FOREIGN KEY (dept_id) REFERENCES public.departments(dept_id) ON DELETE SET NULL;


--
-- Name: admins admins_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: event_docs event_docs_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_docs
    ADD CONSTRAINT event_docs_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(event_id) ON DELETE CASCADE;


--
-- Name: event_docs event_docs_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_docs
    ADD CONSTRAINT event_docs_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: events events_created_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_created_by_fk FOREIGN KEY (created_by) REFERENCES public.admins(admin_id) ON DELETE RESTRICT;


--
-- Name: events events_dept_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_dept_fk FOREIGN KEY (dept_id) REFERENCES public.departments(dept_id) ON DELETE SET NULL;


--
-- Name: events events_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: families families_approved_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_approved_by_fk FOREIGN KEY (approved_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: families families_created_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_created_by_fk FOREIGN KEY (created_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: families families_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: family_members family_members_family_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_family_fk FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE CASCADE;


--
-- Name: family_members family_members_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE CASCADE;


--
-- Name: logs logs_actor_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_actor_fk FOREIGN KEY (actor_id) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: logs logs_event_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_event_fk FOREIGN KEY (event_id) REFERENCES public.events(event_id) ON DELETE SET NULL;


--
-- Name: logs logs_family_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_family_fk FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE SET NULL;


--
-- Name: logs logs_solidarity_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_solidarity_fk FOREIGN KEY (solidarity_id) REFERENCES public.solidarities(solidarity_id) ON DELETE SET NULL;


--
-- Name: prtcps prtcps_event_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_event_fk FOREIGN KEY (event_id) REFERENCES public.events(event_id) ON DELETE CASCADE;


--
-- Name: prtcps prtcps_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE CASCADE;


--
-- Name: solidarities solidarities_approved_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_approved_by_fk FOREIGN KEY (approved_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: solidarities solidarities_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: solidarities solidarities_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE SET NULL;


--
-- Name: solidarity_docs solidarity_docs_solidarity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarity_docs
    ADD CONSTRAINT solidarity_docs_solidarity_id_fkey FOREIGN KEY (solidarity_id) REFERENCES public.solidarities(solidarity_id) ON DELETE CASCADE;


--
-- Name: students students_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict P5EnfxzXpcYUdWOz3a8epJmeMwu9TZAXKGV7GpFxe2C0dng9FurSHMIXWeGLIHU

