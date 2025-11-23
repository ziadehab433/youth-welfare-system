--
-- PostgreSQL database dump
--

\restrict 4bMd84xQA5eS0yMqYHAsaaJg1120es5YZM2qQ5eIjLotMdFOsPoZdK84S8p5Qat

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
    'طالب',
    'مدير ادارة'
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
    'حبازة زراعية',
    'تكافل و كرامة'
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
DECLARE
    admin_role actor_type ;
BEGIN
    -- Get the role of the admin who approved the solidarity
    SELECT role INTO admin_role FROM admins WHERE admin_id = NEW.approved_by;

    -- Insert log entry with correct field order
    INSERT INTO logs (
        actor_id,
        actor_type,
        action,
        target_type,
        solidarity_id,
        ip_address
    )
    VALUES (
        NEW.approved_by,
        admin_role,          -- ✅ use the variable here
        'موافقة طلب',       -- action
        'تكافل',             
        NEW.solidarity_id,
        client_ip()
    );

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_solidarity_approval() OWNER TO postgres;

--
-- Name: log_solidarity_pre_approval(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_solidarity_pre_approval() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    admin_role actor_type;
BEGIN
    -- Fetch the admin's role from the admins table
    SELECT role INTO admin_role FROM admins WHERE admin_id = NEW.approved_by;

    -- Insert log entry for pre-approval
    INSERT INTO logs (
        actor_id,
        actor_type,
        action,
        target_type,
        solidarity_id,
        ip_address
    )
    VALUES (
        NEW.approved_by,    
        admin_role,         
        'موافقة مبدئية',     
        'تكافل',             
        NEW.solidarity_id,
        client_ip()          
    );

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_solidarity_pre_approval() OWNER TO postgres;

--
-- Name: log_solidarity_rejection(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_solidarity_rejection() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    admin_role actor_type;
BEGIN
    -- Fetch the admin's role from the admins table
    SELECT role INTO admin_role FROM admins WHERE admin_id = NEW.approved_by;

    -- Insert log entry for rejection
    INSERT INTO logs (
        actor_id,
        actor_type,
        action,
        target_type,
        solidarity_id,
        ip_address
    )
    VALUES (
        NEW.approved_by,     -- ID of the admin who rejected
        admin_role,          -- ✅ store their role here
        'رفض طلب',           -- action text (rejection)
        'تكافل',             -- target type
        NEW.solidarity_id,
        client_ip()
    );

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
    password text NOT NULL,
    faculty_id integer,
    dept_id integer,
    created_at timestamp with time zone DEFAULT now(),
    can_create boolean DEFAULT false,
    can_update boolean DEFAULT false,
    can_read boolean DEFAULT true,
    can_delete boolean DEFAULT false,
    acc_status character varying(20) DEFAULT 'active'::character varying,
    role public.admin_role,
    dept_fac_ls text[] DEFAULT '{}'::text[]
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
    major text[] NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    aff_discount real[],
    reg_discount double precision[],
    bk_discount double precision[],
    full_discount double precision[]
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
    total_discount double precision,
    sd character(1) DEFAULT 'f'::bpchar NOT NULL,
    discount_type text[] DEFAULT '{}'::text[],
    CONSTRAINT solidarities_f_phone_num_check CHECK (((f_phone_num IS NULL) OR (f_phone_num ~ '^\+?[0-9]{6,15}$'::text))),
    CONSTRAINT solidarities_m_phone_num_check CHECK (((m_phone_num IS NULL) OR (m_phone_num ~ '^\+?[0-9]{6,15}$'::text))),
    CONSTRAINT solidarities_sd_check CHECK ((sd = ANY (ARRAY['t'::bpchar, 'f'::bpchar])))
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
    mime_type character varying(80) NOT NULL,
    file_size integer,
    uploaded_at timestamp with time zone DEFAULT now(),
    file character varying(255)
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
    password text NOT NULL,
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

COPY public.admins (admin_id, name, email, password, faculty_id, dept_id, created_at, can_create, can_update, can_read, can_delete, acc_status, role, dept_fac_ls) FROM stdin;
4	سارة محمد	sara.head@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	1	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير كلية	{}
6	منى يوسف	mona.general@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير عام	{}
8	omar	omar@gmail.com	pbkdf2_sha256$1000000$vlZHhPpW9IpNAdiVAlRLoZ$EKZZMi53hEdx/k1aLRSkqXWKnmZgVcXUMN0N8tP7RNQ=	1	\N	2025-10-30 01:10:42.356929+03	t	t	t	t	active	مسؤول كلية	{string,"فني و ثقافي"}
12	string	user@example.com	pbkdf2_sha256$1000000$IrRY86mbOwprrogP9aOI2H$2RgAvUXSAwxSeNHNhdSuu+RXGdAhwr9bghYxx5mvfZY=	1	1	2025-11-15 03:13:03.29534+02	t	t	t	t	active	مسؤول كلية	{}
13	string	admin@example.com	pbkdf2_sha256$1000000$QvWcdHW5PZf3birfhgr1K1$ze8CXVUv+iOXUkR+zOGt0dx9HGx9I5Tsl47DoOmL4KY=	\N	\N	2025-11-15 03:30:33.532263+02	t	t	t	t	string	مشرف النظام	{}
14	a4	ar@gmail.com.com	pbkdf2_sha256$1000000$zBktzHX9eDrOqSc9VSreRz$eFZqgCmqCYdzJ7TUfKZQoUaOXXPxgicfH1cyjNL31dQ=	\N	\N	2025-11-15 03:36:53.711315+02	t	t	t	t	active	مشرف النظام	{}
15	ali	alioamar@gmail.com	pbkdf2_sha256$1000000$MYace5Oq8w4z1fOtwxrC3A$d8Vh8UhpL/6nKz4RcdwtRDIWAoso5ZxHTELq+wOJfMs=	1	\N	2025-11-18 20:27:49.844806+02	t	t	t	t	active	مسؤول كلية	{"نشاط فني","نشاط رياضي"}
16	oo	oo@gmail.com	pbkdf2_sha256$1000000$QXXplajwQLlKBLRkvWyEDG$j2Hy8tqFThcTmWs+C0g6pFfGvVtrklz/leeYU9X0WzI=	\N	2	2025-11-18 20:45:57.231286+02	t	t	t	t	active	مدير ادارة	{تكافل}
17	aa	aa@gmail.com	pbkdf2_sha256$1000000$2dc1qpkT0K2Rvf8jYCZFGr$RYI8fid0TOn0KPMmVGLXDSb+4fCh2gtoN+F/KrCJ0RE=	2	\N	2025-11-18 21:42:50.130782+02	t	t	t	t	active	مسؤول كلية	{"نشاط فمي",تكافل}
18	admin12	admin12@gmail.com	pbkdf2_sha256$1000000$sZ9BCWoeUQKBmW1h4mY3g8$QqXoHVTnnHG6Xtk3BeqX21BCFPeh1zN6RD1cWtz/Ads=	2	\N	2025-11-18 23:03:16.0987+02	t	t	t	t	نشط	مسؤول كلية	{"فني و رياضي",رياضي}
1	ahmed	ahmed@gmail.com	pbkdf2_sha256$1000000$dx0GL2Uj1qVCDZa7x83045$0q9vmyfE+Bf0237qGzyUVvtqnJEauuW6eauxJra+CIM=	1	\N	2025-10-20 02:34:30.31113+03	t	t	t	t	active	مسؤول كلية	{"نشاط فني و ثقافي"}
3	أحمد علي	ahmed.faculty@example.com	pbkdf2_sha256$1000000$k0IQx82TzGMhVAFEe6Y8Zl$oiR9QGJQIceP5VudDGMnLBdeXYfJPbgW1rmeNzobO0g=	3	\N	2025-10-20 02:53:23.217139+03	t	t	t	f	active	مسؤول كلية	{}
19	admin33	admin33@example.com	pbkdf2_sha256$1000000$rEqE9UmuMQqskvYGjne6Nd$T0ST6Ew8rabU2sFpgL/o90T4uhB8PUvkNCzOOOYIUI4=	2	\N	2025-11-21 16:33:42.63292+02	t	t	t	t	active	مسؤول كلية	{فني,رياضي}
20	admin34	admin34@example.com	pbkdf2_sha256$1000000$WqUSKaWUHuPX89VGicr9jA$La3PHY+349r/DeTyaXSvAoO3K3S5JvzcI/I7rq2ltVk=	2	\N	2025-11-21 16:34:27.807083+02	t	t	t	t	active	مسؤول كلية	{فني,رياضي,ثقافي}
7	محمد سعيد	mohamed.super@example.com	pbkdf2_sha256$1000000$yOdSWDrX15vKLosN6Dp41Y$I5NAsjlV29vxASgyoBCPnikiCcl9wf9fPvCxXSHt4Ys=	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مشرف النظام	{}
9	ali	ali@gmail.com	pbkdf2_sha256$1000000$g5LSEHFQAOV5imJXliaDcS$EC34z7cDVSgQjTbt3313xwvXrj72TCS+GExZENNjMI4=	1	\N	2025-10-30 01:34:00.847159+03	t	t	t	t	active	مسؤول كلية	{"فني و ثقافي",رياضي}
5	خالد إبراهيم	khaled.manager@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	\N	1	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير ادارة	{}
11	B	B@gmail.com	pbkdf2_sha256$1000000$wrgC5ZDwinGSr1g0SR8vrz$RZ3Xy50cG9qhkw+toLxLTBdGpMndW5G/SgY3Iewb9EE=	\N	\N	2025-10-30 02:09:47.364118+03	t	t	t	t	active	مشرف النظام	{}
10	A	A@gmail.com	pbkdf2_sha256$1000000$wN2OdjwYyuKZ9kKEjKkhPH$LMzBhFiIGlM6QlllHD9z+PtdJd1aF0hNRQdCTFJgYRY=	\N	\N	2025-10-30 01:37:07.429515+03	t	t	t	t	active	مشرف النظام	{}
2	سارة محمد	sara@example.com	pbkdf2_sha256$1000000$YOum6XQm4YPTyOygoretCH$qI6iJdP+RHVI5jCneq2CYhb88PnvNhsdvduSklDyMaI=	2	\N	2025-10-20 02:34:30.31113+03	t	t	t	f	active	مسؤول كلية	{"فني و ثقافي"}
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
25	Can add faculties	7	add_faculties
26	Can change faculties	7	change_faculties
27	Can delete faculties	7	delete_faculties
28	Can view faculties	7	view_faculties
29	Can add departments	8	add_departments
30	Can change departments	8	change_departments
31	Can delete departments	8	delete_departments
32	Can view departments	8	view_departments
33	Can add admins	9	add_admins
34	Can change admins	9	change_admins
35	Can delete admins	9	delete_admins
36	Can view admins	9	view_admins
37	Can add students	10	add_students
38	Can change students	10	change_students
39	Can delete students	10	delete_students
40	Can view students	10	view_students
41	Can add events	11	add_events
42	Can change events	11	change_events
43	Can delete events	11	delete_events
44	Can view events	11	view_events
45	Can add families	12	add_families
46	Can change families	12	change_families
47	Can delete families	12	delete_families
48	Can view families	12	view_families
49	Can add family members	13	add_familymembers
50	Can change family members	13	change_familymembers
51	Can delete family members	13	delete_familymembers
52	Can view family members	13	view_familymembers
53	Can add solidarities	14	add_solidarities
54	Can change solidarities	14	change_solidarities
55	Can delete solidarities	14	delete_solidarities
56	Can view solidarities	14	view_solidarities
57	Can add documents	15	add_documents
58	Can change documents	15	change_documents
59	Can delete documents	15	delete_documents
60	Can view documents	15	view_documents
61	Can add logs	16	add_logs
62	Can change logs	16	change_logs
63	Can delete logs	16	delete_logs
64	Can view logs	16	view_logs
65	Can add prtcps	17	add_prtcps
66	Can change prtcps	17	change_prtcps
67	Can delete prtcps	17	delete_prtcps
68	Can view prtcps	17	view_prtcps
69	Can add events	18	add_events
70	Can change events	18	change_events
71	Can delete events	18	delete_events
72	Can view events	18	view_events
73	Can add solidarities	19	add_solidarities
74	Can change solidarities	19	change_solidarities
75	Can delete solidarities	19	delete_solidarities
76	Can view solidarities	19	view_solidarities
77	Can add logs	20	add_logs
78	Can change logs	20	change_logs
79	Can delete logs	20	delete_logs
80	Can view logs	20	view_logs
81	Can add solidarity docs	21	add_solidaritydocs
82	Can change solidarity docs	21	change_solidaritydocs
83	Can delete solidarity docs	21	delete_solidaritydocs
84	Can view solidarity docs	21	view_solidaritydocs
85	Can add departments	22	add_departments
86	Can change departments	22	change_departments
87	Can delete departments	22	delete_departments
88	Can view departments	22	view_departments
89	Can add students	23	add_students
90	Can change students	23	change_students
91	Can delete students	23	delete_students
92	Can view students	23	view_students
93	Can add faculties	24	add_faculties
94	Can change faculties	24	change_faculties
95	Can delete faculties	24	delete_faculties
96	Can view faculties	24	view_faculties
97	Can add admins	25	add_admins
98	Can change admins	25	change_admins
99	Can delete admins	25	delete_admins
100	Can view admins	25	view_admins
101	Can add families	26	add_families
102	Can change families	26	change_families
103	Can delete families	26	delete_families
104	Can view families	26	view_families
105	Can add admins user	27	add_adminsuser
106	Can change admins user	27	change_adminsuser
107	Can delete admins user	27	delete_adminsuser
108	Can view admins user	27	view_adminsuser
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
7	youth_welfare	faculties
8	youth_welfare	departments
9	youth_welfare	admins
10	youth_welfare	students
11	youth_welfare	events
12	youth_welfare	families
13	youth_welfare	familymembers
14	youth_welfare	solidarities
15	youth_welfare	documents
16	youth_welfare	logs
17	youth_welfare	prtcps
18	event	events
19	solidarity	solidarities
20	solidarity	logs
21	solidarity	solidaritydocs
22	solidarity	departments
23	solidarity	students
24	solidarity	faculties
25	solidarity	admins
26	family	families
27	accounts	adminsuser
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2025-10-11 20:19:28.802694+03
2	auth	0001_initial	2025-10-11 20:19:28.855341+03
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
19	accounts	0001_initial	2025-11-09 22:13:47.297098+02
20	admin	0001_initial	2025-11-09 22:16:49.456779+02
21	admin	0002_logentry_remove_auto_add	2025-11-09 22:16:49.462668+02
22	admin	0003_logentry_add_action_flag_choices	2025-11-09 22:16:49.466561+02
23	solidarity	0001_initial	2025-11-09 22:36:23.382084+02
24	solidarity	0002_departments_solidaritydocs	2025-11-09 23:54:25.523197+02
25	solidarity	0003_alter_solidaritydocs_file	2025-11-09 23:54:25.524607+02
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

COPY public.faculties (faculty_id, name, major, created_at, aff_discount, reg_discount, bk_discount, full_discount) FROM stdin;
3	الطب	{البشري}	2025-10-25 22:28:16.437365+03	{100}	{200}	{300}	{400}
2	كلية العلوم	{"علوم أساسية"}	2025-10-20 02:34:30.31113+03	{400}	{300}	{200}	{100}
1	كلية الهندسة	{"هندسة عامة"}	2025-10-20 02:34:30.31113+03	{100,200,300}	{1000,2500}	{400,700}	{5000}
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
1	2	موافقة مبدئية	\N	1	\N	::1	2025-10-27 18:05:54.950216+03	\N	تكافل
2	2	موافقة طلب	\N	1	\N	::1	2025-10-27 18:07:26.369455+03	\N	تكافل
3	7	رفض طلب	\N	1	\N	::1	2025-10-27 18:09:06.426822+03	\N	تكافل
4	7	موافقة طلب	\N	1	\N	::1	2025-10-27 18:16:00.824412+03	\N	تكافل
5	7	رفض طلب	\N	1	\N	::1	2025-10-27 18:32:40.341603+03	\N	تكافل
6	7	موافقة طلب	\N	1	\N	::1	2025-10-27 18:46:47.99384+03	مشرف النظام	تكافل
7	7	رفض طلب	\N	1	\N	::1	2025-10-27 18:48:54.354514+03	\N	تكافل
8	7	موافقة طلب	\N	1	\N	::1	2025-10-27 18:51:45.940122+03	مشرف النظام	تكافل
9	7	رفض طلب	\N	1	\N	::1	2025-10-27 18:51:50.370914+03	مشرف النظام	تكافل
10	2	موافقة مبدئية	\N	1	\N	::1	2025-10-27 18:53:33.431637+03	\N	تكافل
11	2	موافقة طلب	\N	1	\N	::1	2025-10-27 18:54:01.519844+03	مسؤول كلية	تكافل
12	2	موافقة مبدئية	\N	1	\N	::1	2025-10-27 19:03:25.333497+03	مسؤول كلية	تكافل
13	2	موافقة طلب	\N	1	\N	::1	2025-10-27 19:06:20.936167+03	مسؤول كلية	تكافل
15	7	رفض طلب	\N	2	\N	::1	2025-10-28 01:02:03.629864+03	مشرف النظام	تكافل
16	7	رفض طلب	\N	1	\N	::1	2025-10-28 01:11:20.27337+03	مشرف النظام	تكافل
17	7	رفض طلب	\N	3	\N	::1	2025-10-28 01:14:47.758265+03	مشرف النظام	تكافل
18	7	رفض طلب	\N	4	\N	::1	2025-10-28 01:19:53.839019+03	مشرف النظام	تكافل
19	7	رفض طلب	\N	5	\N	::1	2025-10-28 01:21:07.755414+03	مشرف النظام	تكافل
20	7	رفض طلب	\N	6	\N	::1	2025-10-28 01:24:50.378357+03	مشرف النظام	تكافل
21	8	موافقة مبدئية	\N	8	\N	::1	2025-10-30 18:43:26.427686+03	مسؤول كلية	تكافل
22	8	موافقة طلب	\N	8	\N	::1	2025-10-30 18:44:28.502558+03	مسؤول كلية	تكافل
23	8	رفض طلب	\N	8	\N	::1	2025-10-30 18:45:22.353861+03	مسؤول كلية	تكافل
24	11	موافقة طلب	\N	8	\N	::1	2025-10-30 18:47:35.671758+03	مشرف النظام	تكافل
25	11	رفض طلب	\N	8	\N	::1	2025-10-30 18:47:49.773611+03	مشرف النظام	تكافل
26	11	عرض مستندات الطلب	\N	9	\N	::1	2025-11-07 21:23:50.182872+02	مشرف النظام	تكافل
27	11	عرض بيانات الطلب	\N	9	\N	::1	2025-11-07 21:24:22.508342+02	مشرف النظام	تكافل
28	11	عرض بيانات الطلب	\N	9	\N	::1	2025-11-07 21:38:56.185119+02	مشرف النظام	تكافل
29	2	عرض مستندات الطلب	\N	9	\N	::1	2025-11-07 21:55:40.262796+02	مسؤول كلية	تكافل
30	2	عرض مستندات الطلب	\N	9	\N	\N	2025-11-07 21:58:43.182619+02	مسؤول كلية	تكافل
31	2	عرض مستندات الطلب	\N	9	\N	127.0.0.1	2025-11-07 21:59:12.340907+02	مسؤول كلية	تكافل
32	2	عرض مستندات الطلب	\N	9	\N	127.0.0.1	2025-11-07 21:59:26.833515+02	مسؤول كلية	تكافل
33	2	عرض مستندات الطلب	\N	9	\N	127.0.0.1	2025-11-07 21:59:32.929871+02	مسؤول كلية	تكافل
34	2	عرض بيانات الطلب	\N	7	\N	127.0.0.1	2025-11-07 22:04:20.19844+02	مسؤول كلية	تكافل
35	8	عرض بيانات الطلب	\N	8	\N	127.0.0.1	2025-11-08 17:05:48.719094+02	مسؤول كلية	تكافل
36	8	عرض مستندات الطلب	\N	8	\N	127.0.0.1	2025-11-08 17:06:37.917357+02	مسؤول كلية	تكافل
37	11	عرض مستندات الطلب	\N	8	\N	127.0.0.1	2025-11-08 23:30:49.561543+02	مشرف النظام	تكافل
38	11	عرض بيانات الطلب	\N	8	\N	127.0.0.1	2025-11-08 23:31:21.872489+02	مشرف النظام	تكافل
39	11	رفض طلب	\N	9	\N	::1	2025-11-09 16:27:58.071106+02	مشرف النظام	تكافل
40	11	عرض مستندات الطلب	\N	12	\N	127.0.0.1	2025-11-09 23:21:37.497281+02	مشرف النظام	تكافل
41	11	رفض طلب	\N	12	\N	::1	2025-11-09 23:25:42.439857+02	مشرف النظام	تكافل
43	11	رفض طلب	\N	7	\N	::1	2025-11-09 23:32:48.53273+02	مشرف النظام	تكافل
44	11	رفض طلب	\N	13	\N	::1	2025-11-09 23:35:01.626461+02	مشرف النظام	تكافل
45	11	رفض طلب	\N	14	\N	::1	2025-11-09 23:36:37.185503+02	مشرف النظام	تكافل
46	11	رفض طلب	\N	15	\N	::1	2025-11-09 23:45:31.849727+02	مشرف النظام	تكافل
47	11	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-09 23:46:47.538212+02	مشرف النظام	تكافل
48	11	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-09 23:54:38.451039+02	مشرف النظام	تكافل
49	11	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-09 23:56:05.98687+02	مشرف النظام	تكافل
50	8	عرض بيانات الطلب	\N	16	\N	127.0.0.1	2025-11-10 02:49:09.998394+02	مسؤول كلية	تكافل
51	8	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 02:49:24.588758+02	مسؤول كلية	تكافل
52	3	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 02:51:22.594827+02	مسؤول كلية	تكافل
53	3	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 02:51:24.768662+02	مسؤول كلية	تكافل
54	3	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 02:54:23.735011+02	مسؤول كلية	تكافل
55	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 02:54:42.876884+02	مسؤول كلية	تكافل
56	3	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-10 02:56:32.874011+02	مسؤول كلية	تكافل
57	3	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 02:56:40.848563+02	مسؤول كلية	تكافل
58	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 02:56:56.762458+02	مسؤول كلية	تكافل
59	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:00:32.668675+02	مسؤول كلية	تكافل
60	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:00:37.248913+02	مسؤول كلية	تكافل
61	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:01:12.742637+02	مسؤول كلية	تكافل
62	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:01:13.638661+02	مسؤول كلية	تكافل
63	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:11:25.18831+02	مسؤول كلية	تكافل
64	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:16:05.16354+02	مسؤول كلية	تكافل
65	3	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:20:23.814193+02	مسؤول كلية	تكافل
66	11	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:23:05.132268+02	مشرف النظام	تكافل
67	11	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-10 03:26:52.623963+02	مشرف النظام	تكافل
68	11	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-10 03:27:25.854259+02	مشرف النظام	تكافل
69	11	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 03:27:32.615915+02	مشرف النظام	تكافل
70	11	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 03:28:12.392138+02	مشرف النظام	تكافل
71	11	عرض مستندات الطلب	\N	16	\N	127.0.0.1	2025-11-10 03:28:13.630016+02	مشرف النظام	تكافل
72	11	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-14 16:51:16.039507+02	مشرف النظام	تكافل
73	8	موافقة طلب	\N	20	\N	::1	2025-11-16 02:19:03.550234+02	مسؤول كلية	تكافل
74	8	موافقة طلب	\N	21	\N	::1	2025-11-16 02:19:08.719275+02	مسؤول كلية	تكافل
75	8	موافقة طلب	\N	22	\N	::1	2025-11-16 02:19:13.827147+02	مسؤول كلية	تكافل
76	8	موافقة طلب	\N	23	\N	::1	2025-11-16 02:19:18.238806+02	مسؤول كلية	تكافل
77	5	عرض بيانات الطلب	\N	22	\N	127.0.0.1	2025-11-18 18:22:22.814192+02	مدير ادارة	تكافل
78	5	عرض بيانات الطلب	\N	17	\N	127.0.0.1	2025-11-18 21:30:27.706821+02	مدير ادارة	تكافل
79	5	عرض بيانات الطلب	\N	17	\N	127.0.0.1	2025-11-18 21:35:06.933301+02	مدير ادارة	تكافل
80	5	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-18 21:35:30.166683+02	مدير ادارة	تكافل
81	5	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2025-11-18 21:35:44.135581+02	مدير ادارة	تكافل
82	5	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2025-11-18 21:35:46.89413+02	مدير ادارة	تكافل
83	5	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-18 21:35:52.661333+02	مدير ادارة	تكافل
84	5	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-18 21:46:31.464065+02	مدير ادارة	تكافل
85	5	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-18 21:46:42.746983+02	مدير ادارة	تكافل
86	5	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2025-11-18 21:46:53.643884+02	مدير ادارة	تكافل
87	5	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-18 21:48:41.507058+02	مدير ادارة	تكافل
88	5	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-18 21:48:43.455478+02	مدير ادارة	تكافل
89	3	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-19 18:29:45.143425+02	مسؤول كلية	تكافل
90	3	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-19 18:42:26.340674+02	مسؤول كلية	تكافل
91	15	موافقة طلب	\N	24	\N	::1	2025-11-19 21:48:25.86762+02	مسؤول كلية	تكافل
92	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-20 15:42:44.189167+02	مسؤول كلية	تكافل
93	8	عرض بيانات الطلب	\N	16	\N	127.0.0.1	2025-11-21 19:52:26.351729+02	مسؤول كلية	تكافل
94	8	موافقة مبدئية	\N	16	\N	::1	2025-11-21 19:53:15.051296+02	مسؤول كلية	تكافل
95	8	موافقة طلب	\N	16	\N	::1	2025-11-21 19:58:22.574596+02	مسؤول كلية	تكافل
96	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-21 20:06:50.237292+02	مسؤول كلية	تكافل
97	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-21 20:16:13.825153+02	مسؤول كلية	تكافل
98	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-21 20:25:46.327653+02	مسؤول كلية	تكافل
99	8	موافقة طلب	\N	24	\N	::1	2025-11-21 20:35:29.050078+02	مسؤول كلية	تكافل
100	8	عرض بيانات الطلب	\N	16	\N	127.0.0.1	2025-11-21 21:04:07.967264+02	مسؤول كلية	تكافل
101	8	عرض بيانات الطلب	\N	16	\N	127.0.0.1	2025-11-21 21:09:45.675534+02	مسؤول كلية	تكافل
102	8	عرض بيانات الطلب	\N	9	\N	127.0.0.1	2025-11-21 22:03:18.673263+02	مسؤول كلية	تكافل
103	8	عرض بيانات الطلب	\N	9	\N	127.0.0.1	2025-11-22 00:05:16.833455+02	مسؤول كلية	تكافل
104	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 00:05:54.390464+02	مسؤول كلية	تكافل
105	8	عرض بيانات الطلب	\N	9	\N	127.0.0.1	2025-11-22 00:10:06.158608+02	مسؤول كلية	تكافل
106	8	موافقة طلب	\N	9	\N	::1	2025-11-22 00:21:18.300216+02	مسؤول كلية	تكافل
107	8	عرض بيانات الطلب	\N	9	\N	127.0.0.1	2025-11-22 00:34:40.7202+02	مسؤول كلية	تكافل
109	8	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:06:37.870772+02	مسؤول كلية	تكافل
108	8	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:06:37.871305+02	مسؤول كلية	تكافل
110	8	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:06:37.97477+02	مسؤول كلية	تكافل
111	8	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:06:37.982425+02	مسؤول كلية	تكافل
112	8	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:07:14.166935+02	مسؤول كلية	تكافل
113	8	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:07:14.180893+02	مسؤول كلية	تكافل
114	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:11:58.533293+02	مسؤول كلية	تكافل
115	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:11:58.549846+02	مسؤول كلية	تكافل
116	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:11:58.626375+02	مسؤول كلية	تكافل
117	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:11:58.630723+02	مسؤول كلية	تكافل
118	12	رفض طلب	\N	26	\N	::1	2025-11-22 18:12:01.346154+02	مسؤول كلية	تكافل
119	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:01.415594+02	مسؤول كلية	تكافل
120	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:02.076628+02	مسؤول كلية	تكافل
121	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:02.087513+02	مسؤول كلية	تكافل
122	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:17.846259+02	مسؤول كلية	تكافل
123	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:17.848695+02	مسؤول كلية	تكافل
124	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:17.850487+02	مسؤول كلية	تكافل
125	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:17.923392+02	مسؤول كلية	تكافل
126	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:45.139713+02	مسؤول كلية	تكافل
127	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:45.153992+02	مسؤول كلية	تكافل
128	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:45.166576+02	مسؤول كلية	تكافل
129	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:45.236303+02	مسؤول كلية	تكافل
130	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:56.0983+02	مسؤول كلية	تكافل
131	12	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:56.109186+02	مسؤول كلية	تكافل
132	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:56.119396+02	مسؤول كلية	تكافل
133	12	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 18:12:56.194742+02	مسؤول كلية	تكافل
134	12	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-11-22 18:13:13.897141+02	مسؤول كلية	تكافل
135	12	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-11-22 18:13:13.898486+02	مسؤول كلية	تكافل
136	12	عرض بيانات الطلب	\N	25	\N	127.0.0.1	2025-11-22 18:13:13.898887+02	مسؤول كلية	تكافل
137	12	عرض بيانات الطلب	\N	25	\N	127.0.0.1	2025-11-22 18:13:13.906949+02	مسؤول كلية	تكافل
138	12	رفض طلب	\N	25	\N	::1	2025-11-22 18:13:29.627543+02	مسؤول كلية	تكافل
139	12	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-11-22 18:13:29.796324+02	مسؤول كلية	تكافل
140	12	عرض بيانات الطلب	\N	25	\N	127.0.0.1	2025-11-22 18:13:30.402517+02	مسؤول كلية	تكافل
141	12	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-11-22 18:13:30.410219+02	مسؤول كلية	تكافل
142	7	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 20:13:54.902411+02	مشرف النظام	تكافل
143	7	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 20:13:54.908029+02	مشرف النظام	تكافل
144	7	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2025-11-22 20:13:54.97394+02	مشرف النظام	تكافل
145	7	عرض بيانات الطلب	\N	26	\N	127.0.0.1	2025-11-22 20:13:55.093798+02	مشرف النظام	تكافل
146	8	عرض بيانات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:16.228637+02	مسؤول كلية	تكافل
147	8	عرض بيانات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:16.291339+02	مسؤول كلية	تكافل
148	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:16.329153+02	مسؤول كلية	تكافل
149	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:16.491548+02	مسؤول كلية	تكافل
150	8	موافقة مبدئية	\N	27	\N	::1	2025-11-22 21:11:25.391667+02	مسؤول كلية	تكافل
151	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:25.457071+02	مسؤول كلية	تكافل
152	8	عرض بيانات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:25.928061+02	مسؤول كلية	تكافل
153	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:25.934025+02	مسؤول كلية	تكافل
154	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:34.125884+02	مسؤول كلية	تكافل
155	8	موافقة طلب	\N	27	\N	::1	2025-11-22 21:11:35.528508+02	مسؤول كلية	تكافل
156	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:35.589279+02	مسؤول كلية	تكافل
157	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:36.022245+02	مسؤول كلية	تكافل
158	8	عرض بيانات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:36.104223+02	مسؤول كلية	تكافل
159	8	عرض بيانات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:44.115302+02	مسؤول كلية	تكافل
160	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:44.126097+02	مسؤول كلية	تكافل
161	8	عرض بيانات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:44.187379+02	مسؤول كلية	تكافل
162	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2025-11-22 21:11:44.299836+02	مسؤول كلية	تكافل
163	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:11:54.942648+02	مسؤول كلية	تكافل
164	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:11:54.951802+02	مسؤول كلية	تكافل
165	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:11:55.010936+02	مسؤول كلية	تكافل
166	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:11:55.017933+02	مسؤول كلية	تكافل
167	8	موافقة مبدئية	\N	24	\N	::1	2025-11-22 21:11:57.462635+02	مسؤول كلية	تكافل
168	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:11:57.522197+02	مسؤول كلية	تكافل
169	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:11:57.959156+02	مسؤول كلية	تكافل
170	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:11:57.972363+02	مسؤول كلية	تكافل
171	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:12:06.752977+02	مسؤول كلية	تكافل
172	8	موافقة طلب	\N	24	\N	::1	2025-11-22 21:12:08.357331+02	مسؤول كلية	تكافل
173	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:12:08.414827+02	مسؤول كلية	تكافل
174	8	عرض بيانات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:12:08.852052+02	مسؤول كلية	تكافل
175	8	عرض مستندات الطلب	\N	24	\N	127.0.0.1	2025-11-22 21:12:08.86452+02	مسؤول كلية	تكافل
176	8	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:12:36.666401+02	مسؤول كلية	تكافل
177	8	عرض بيانات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:12:36.767041+02	مسؤول كلية	تكافل
178	8	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:12:36.832951+02	مسؤول كلية	تكافل
179	8	عرض بيانات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:12:36.930114+02	مسؤول كلية	تكافل
180	8	موافقة مبدئية	\N	14	\N	::1	2025-11-22 21:12:38.732583+02	مسؤول كلية	تكافل
181	8	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:12:38.894983+02	مسؤول كلية	تكافل
182	8	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:12:39.326084+02	مسؤول كلية	تكافل
183	8	عرض بيانات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:12:39.33966+02	مسؤول كلية	تكافل
184	8	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:13:02.373766+02	مسؤول كلية	تكافل
185	8	موافقة طلب	\N	14	\N	::1	2025-11-22 21:13:04.029127+02	مسؤول كلية	تكافل
186	8	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:13:04.184652+02	مسؤول كلية	تكافل
187	8	عرض بيانات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:13:04.588375+02	مسؤول كلية	تكافل
188	8	عرض مستندات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:13:04.594467+02	مسؤول كلية	تكافل
189	8	عرض بيانات الطلب	\N	14	\N	127.0.0.1	2025-11-22 21:14:45.459046+02	مسؤول كلية	تكافل
190	8	عرض بيانات الطلب	\N	13	\N	127.0.0.1	2025-11-22 21:15:23.083162+02	مسؤول كلية	تكافل
191	8	عرض بيانات الطلب	\N	23	\N	127.0.0.1	2025-11-22 21:18:39.705608+02	مسؤول كلية	تكافل
192	8	عرض بيانات الطلب	\N	23	\N	127.0.0.1	2025-11-22 21:18:39.772251+02	مسؤول كلية	تكافل
193	8	موافقة مبدئية	\N	23	\N	::1	2025-11-22 21:18:42.773535+02	مسؤول كلية	تكافل
194	8	عرض بيانات الطلب	\N	23	\N	127.0.0.1	2025-11-22 21:18:43.278017+02	مسؤول كلية	تكافل
195	8	عرض بيانات الطلب	\N	23	\N	127.0.0.1	2025-11-22 21:19:01.5079+02	مسؤول كلية	تكافل
196	8	عرض بيانات الطلب	\N	22	\N	127.0.0.1	2025-11-22 21:19:56.611376+02	مسؤول كلية	تكافل
197	8	عرض بيانات الطلب	\N	22	\N	127.0.0.1	2025-11-22 21:19:56.674855+02	مسؤول كلية	تكافل
198	8	عرض بيانات الطلب	\N	13	\N	127.0.0.1	2025-11-22 21:20:03.277405+02	مسؤول كلية	تكافل
199	8	عرض بيانات الطلب	\N	13	\N	127.0.0.1	2025-11-22 21:20:03.343544+02	مسؤول كلية	تكافل
200	8	عرض بيانات الطلب	\N	8	\N	127.0.0.1	2025-11-22 21:20:15.25057+02	مسؤول كلية	تكافل
201	8	عرض بيانات الطلب	\N	8	\N	127.0.0.1	2025-11-22 21:20:15.3164+02	مسؤول كلية	تكافل
202	8	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-11-22 21:21:46.414071+02	مسؤول كلية	تكافل
203	8	عرض بيانات الطلب	\N	25	\N	127.0.0.1	2025-11-22 21:21:46.418079+02	مسؤول كلية	تكافل
204	8	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-11-22 21:21:46.481017+02	مسؤول كلية	تكافل
205	8	عرض بيانات الطلب	\N	25	\N	127.0.0.1	2025-11-22 21:21:46.485668+02	مسؤول كلية	تكافل
206	11	عرض بيانات الطلب	\N	1	\N	127.0.0.1	2025-11-22 21:22:46.649059+02	مشرف النظام	تكافل
207	11	عرض بيانات الطلب	\N	1	\N	127.0.0.1	2025-11-22 21:22:46.80624+02	مشرف النظام	تكافل
208	11	موافقة طلب	\N	1	\N	::1	2025-11-22 21:22:48.621488+02	مشرف النظام	تكافل
209	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:25:35.235562+02	مسؤول كلية	تكافل
210	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:25:35.237966+02	مسؤول كلية	تكافل
211	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:25:35.30315+02	مسؤول كلية	تكافل
212	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:25:35.307437+02	مسؤول كلية	تكافل
213	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:25:57.954129+02	مسؤول كلية	تكافل
214	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:04.363632+02	مسؤول كلية	تكافل
215	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:04.366046+02	مسؤول كلية	تكافل
216	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:04.438509+02	مسؤول كلية	تكافل
217	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:04.534003+02	مسؤول كلية	تكافل
218	8	موافقة مبدئية	\N	28	\N	::1	2025-11-22 21:26:05.637122+02	مسؤول كلية	تكافل
219	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:05.694135+02	مسؤول كلية	تكافل
220	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:06.113765+02	مسؤول كلية	تكافل
221	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:06.123924+02	مسؤول كلية	تكافل
222	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:14.807989+02	مسؤول كلية	تكافل
223	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:21.25397+02	مسؤول كلية	تكافل
224	8	موافقة طلب	\N	28	\N	::1	2025-11-22 21:26:29.8242+02	مسؤول كلية	تكافل
225	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:29.996704+02	مسؤول كلية	تكافل
226	8	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:30.413832+02	مسؤول كلية	تكافل
227	8	عرض بيانات الطلب	\N	28	\N	127.0.0.1	2025-11-22 21:26:30.497117+02	مسؤول كلية	تكافل
228	8	عرض بيانات الطلب	\N	22	\N	127.0.0.1	2025-11-22 21:26:50.18592+02	مسؤول كلية	تكافل
229	8	عرض بيانات الطلب	\N	22	\N	127.0.0.1	2025-11-22 21:26:50.265017+02	مسؤول كلية	تكافل
230	8	موافقة مبدئية	\N	22	\N	::1	2025-11-22 21:26:52.326537+02	مسؤول كلية	تكافل
231	8	عرض بيانات الطلب	\N	22	\N	127.0.0.1	2025-11-22 21:26:52.992574+02	مسؤول كلية	تكافل
232	8	عرض بيانات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:42.82411+02	مسؤول كلية	تكافل
233	8	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:42.934131+02	مسؤول كلية	تكافل
234	8	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:42.993568+02	مسؤول كلية	تكافل
235	8	عرض بيانات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:42.995244+02	مسؤول كلية	تكافل
236	8	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:50.170848+02	مسؤول كلية	تكافل
237	8	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:50.236818+02	مسؤول كلية	تكافل
238	8	عرض بيانات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:50.275467+02	مسؤول كلية	تكافل
239	8	عرض بيانات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:50.442659+02	مسؤول كلية	تكافل
240	8	عرض بيانات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:32:56.200138+02	مسؤول كلية	تكافل
241	8	موافقة مبدئية	\N	15	\N	::1	2025-11-22 21:34:07.416895+02	مسؤول كلية	تكافل
242	8	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:34:30.872011+02	مسؤول كلية	تكافل
243	8	عرض بيانات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:34:30.873122+02	مسؤول كلية	تكافل
244	8	عرض مستندات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:34:30.936273+02	مسؤول كلية	تكافل
245	8	عرض بيانات الطلب	\N	15	\N	127.0.0.1	2025-11-22 21:34:31.04806+02	مسؤول كلية	تكافل
246	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:10.4109+02	مسؤول كلية	تكافل
247	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:10.42062+02	مسؤول كلية	تكافل
248	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:10.486799+02	مسؤول كلية	تكافل
249	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:10.488588+02	مسؤول كلية	تكافل
250	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:20.07159+02	مسؤول كلية	تكافل
251	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:20.079134+02	مسؤول كلية	تكافل
252	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:27.593024+02	مسؤول كلية	تكافل
253	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:27.597495+02	مسؤول كلية	تكافل
254	8	موافقة مبدئية	\N	34	\N	::1	2025-11-23 00:02:34.604449+02	مسؤول كلية	تكافل
255	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:34.675587+02	مسؤول كلية	تكافل
256	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:35.169593+02	مسؤول كلية	تكافل
257	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:02:35.172306+02	مسؤول كلية	تكافل
258	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:03:55.140677+02	مسؤول كلية	تكافل
259	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:03:55.231473+02	مسؤول كلية	تكافل
260	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:03:55.242406+02	مسؤول كلية	تكافل
261	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:03:55.402438+02	مسؤول كلية	تكافل
262	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:04:06.205642+02	مسؤول كلية	تكافل
263	8	موافقة طلب	\N	34	\N	::1	2025-11-23 00:04:08.039363+02	مسؤول كلية	تكافل
264	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:04:08.197963+02	مسؤول كلية	تكافل
265	8	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:04:08.700602+02	مسؤول كلية	تكافل
266	8	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:04:08.707175+02	مسؤول كلية	تكافل
267	11	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:05:11.729168+02	مشرف النظام	تكافل
268	11	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:05:11.733986+02	مشرف النظام	تكافل
269	11	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:05:11.793195+02	مشرف النظام	تكافل
270	11	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:05:11.799687+02	مشرف النظام	تكافل
271	11	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:09:08.332898+02	مشرف النظام	تكافل
272	11	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:09:08.339889+02	مشرف النظام	تكافل
273	11	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:09:08.405435+02	مشرف النظام	تكافل
274	11	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:09:08.420184+02	مشرف النظام	تكافل
275	11	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:09:52.825689+02	مشرف النظام	تكافل
276	11	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-11-23 00:09:52.926519+02	مشرف النظام	تكافل
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

COPY public.solidarities (solidarity_id, student_id, faculty_id, req_status, created_at, family_numbers, father_status, mother_status, father_income, mother_income, total_income, arrange_of_brothers, m_phone_num, f_phone_num, reason, disabilities, grade, acd_status, address, approved_by, updated_at, req_type, housing_status, total_discount, sd, discount_type) FROM stdin;
21	13	1	منتظر	2025-11-14 21:41:08.508703+02	1	string	string	7.00	20.00	27.00	1	+10222222	+20122222222	string	لا	string	string	string	8	2025-11-21 20:40:18.667414+02	\N	ملك	300	f	{}
22	13	1	موافقة مبدئية	2025-11-14 21:44:51.430453+02	1	string	string	7.00	20.00	27.00	1	+10222222	+20122222222	string	لا	string	string	string	8	2025-11-22 21:26:52.326537+02	\N	ملك	400	f	{}
8	13	1	منتظر	2025-10-30 18:38:35.565445+03	1	string	string	550174.60	37.00	550211.60	1	+2012548796	+202545888	string	t	string	string	eg	8	2025-11-21 20:40:18.667414+02	\N	ملك	4500	f	{}
34	13	1	مقبول	2025-11-22 23:59:10.150831+02	5	working	working	200.00	200.00	400.00	2	+201245447789	+201225458774	gdfdfgaggfd	نعم	جيد جدا	انتساب	قغسثقش	8	2025-11-23 00:04:08.039363+02	\N	ايجار	1700	f	{"خصم كتاب","خصم انتظام"}
9	13	1	مقبول	2025-11-07 16:33:31.469638+02	1	حي	حي	50.00	5.00	55.00	1	+20355558887	+2054522588	بيس	f	string	string	string	8	2025-11-22 00:21:18.300216+02	\N	ملك	600	f	{"خصم انتظام","خصم كتاب"}
26	22	1	مرفوض	2025-11-22 16:53:59.746127+02	1	string	string	400.00	200.00	600.00	1	201222222	2012366666	string	t	جيد	full	eg	12	2025-11-22 18:12:01.346154+02	\N	ملك	\N	f	{}
7	2	2	مرفوض	2025-10-28 01:24:54.463617+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	11	2025-11-09 23:32:48.53273+02	\N	ملك	\N	f	{}
25	13	1	مرفوض	2025-11-22 01:14:55.497579+02	1	string	string	500.00	100.00	600.00	1	20457888	201244444	string	f	good	full	eg	12	2025-11-22 18:13:29.627543+02	\N	ملك	\N	f	{}
2	2	2	مرفوض	2025-10-28 00:56:10.499315+03	9	حي	حية	50000.00	1000.00	51000.00	2	+201578963214	+201578963214	دعم خصم	no	ممتاز	انتساب	ايجبت	7	2025-10-28 01:02:03.629864+03	\N	ايجار	\N	f	{}
15	13	1	موافقة مبدئية	2025-11-09 23:36:49.313339+02	1	string	string	500.00	400.00	900.00	1	+20155255	+20355555	string	t	string	string	eg	8	2025-11-22 21:34:11.934963+02	\N	ملك	500	f	{"خصم كامل"}
3	2	2	مرفوض	2025-10-28 01:13:32.31247+03	10	حلو	حلوة	100000.00	500000.00	600000.00	7	+201578963214	+201578963214	صاشف	f	جيد جدا	انتظام	ايجيبت	7	2025-10-28 01:14:47.758265+03	\N	ملك	\N	f	{}
4	2	2	مرفوض	2025-10-28 01:17:55.946147+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	7	2025-10-28 01:19:53.839019+03	\N	ملك	\N	f	{}
5	2	2	مرفوض	2025-10-28 01:20:02.365943+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	7	2025-10-28 01:21:07.755414+03	\N	ملك	\N	f	{}
6	2	2	مرفوض	2025-10-28 01:21:12.208124+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	7	2025-10-28 01:24:50.378357+03	\N	ملك	\N	f	{}
14	13	1	مقبول	2025-11-09 23:35:31.418527+02	1	string	string	500.00	400.00	900.00	1	+20155255	+20355555	string	t	string	string	eg	8	2025-11-22 21:13:04.029127+02	\N	ملك	1300	f	{"خصم انتظام","خصم انتساب"}
13	13	1	منتظر	2025-11-09 23:26:39.736181+02	1	string	string	500.00	400.00	900.00	1	+20155255	+20355555	string	t	string	string	eg	8	2025-11-22 21:17:28.462146+02	\N	ملك	500	f	{"خصم كامل"}
17	2	2	منتظر	2025-11-10 03:36:29.746581+02	1	string	string	200.00	200.00	400.00	1	+202558789	+2056797987	string	t	string	string	ed	\N	\N	\N	ملك	\N	f	{}
18	14	2	منتظر	2025-11-14 16:37:31.209661+02	1	string	string	7054.00	9.00	7063.00	1	+202222222	+20122222	string	f	جيد	ناجح	eg	\N	\N	\N	ملك	\N	f	{}
29	13	1	منتظر	2025-11-22 22:07:32.061467+02	5	deceased	retired	200.00	200.00	400.00	2	+201254578525	+201254578545	تننلع,bkghrytrertt	لا	امتياز	انتظام	egjguy	\N	\N	\N	ملك	\N	f	{}
27	22	1	مقبول	2025-11-22 20:38:22.990429+02	5	working	working	200.00	200.00	400.00	2	+201215458777	+201225887745	uit98t7	نعم	امتياز	انتظام	eg	8	2025-11-22 21:11:35.528508+02	\N	ملك	600	f	{"خصم كتاب","خصم انتساب"}
23	13	1	موافقة مبدئية	2025-11-14 21:45:37.041629+02	1	string	string	7.00	20.00	27.00	1	+10222222	+20122222222	string	لا	string	string	string	8	2025-11-22 21:19:42.025501+02	\N	ملك	1700	f	{"خصم كتاب","خصم انتظام"}
1	2	2	مقبول	2025-10-27 18:03:25.391324+03	7	بالمعاش	ربة منزل	700.00	0.00	700.00	2	+201587489632	+201578963214	احتياج الدعم	لا	جيد	ناجح	مصر	11	2025-11-22 21:22:48.621488+02	\N	ملك	400	f	{}
12	13	1	منتظر	2025-11-09 23:20:12.011062+02	1	string	string	500.00	400.00	900.00	1	+20155255	+20355555	string	t	string	string	eg	11	2025-11-21 20:40:18.667414+02	\N	ملك	\N	f	{}
30	13	1	منتظر	2025-11-22 22:19:25.74942+02	20	حي	حي	200.00	200.00	400.00	2	+2012124588	+20121212122	string	t	string	string	string	\N	\N	\N	ملك	\N	f	{}
24	13	1	مقبول	2025-11-18 21:34:50.217294+02	1	string	string	100.00	200.00	300.00	1	+20212457888	+20323231255	string	t	جيد	انتظام	مصر	8	2025-11-22 21:12:08.357331+02	\N	ملك	700	f	{"خصم كتاب","خصم انتساب"}
20	13	1	منتظر	2025-11-14 21:40:33.851539+02	1	string	string	7.00	20.00	27.00	1	+10222222	+20122222222	string		string	string	string	8	2025-11-21 20:40:18.667414+02	\N	ملك	200	f	{}
31	13	1	منتظر	2025-11-22 22:22:11.594283+02	5	deceased	working	200.00	200.00	400.00	2	+201233666665	+201215487784	غثفغثقغغصث	لا	امتياز	انتظام	ايبساسيسبلس	\N	\N	\N	ملك	\N	f	{}
32	13	1	منتظر	2025-11-22 22:23:31.137338+02	5	working	retired	200.00	200.00	400.00	2	+201254578550	+201254578555	بسشبشبش	لا	امتياز	انتظام	قغسثقش	\N	\N	\N	ملك	\N	f	{}
33	13	1	منتظر	2025-11-22 22:38:56.450304+02	20	متوفي	حي	0.00	200.00	200.00	2	+2012124588	+20121212122	string	t	string	string	string	\N	\N	\N	ملك	\N	f	{}
28	22	1	مقبول	2025-11-22 21:25:05.521407+02	5	working	working	200.00	200.00	400.00	2	+201254578545	+201254578555	rture	نعم	امتياز	انتظام	eg	8	2025-11-22 21:26:29.8242+02	\N	ملك	1700	f	{"خصم كتاب","خصم انتظام"}
16	13	1	منتظر	2025-11-09 23:46:04.397043+02	1	string	string	500.00	400.00	900.00	1	+20155255	+20355555	string	t	string	string	eg	8	2025-11-21 21:09:24.807247+02	\N	ملك	600	f	{"خصم انتظام","خصم كتاب"}
\.


--
-- Data for Name: solidarity_docs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.solidarity_docs (doc_id, solidarity_id, doc_type, mime_type, file_size, uploaded_at, file) FROM stdin;
51	14	حبازة زراعية	image/png	145558	2025-11-09 23:35:31.419656+02	uploads/solidarity/14/postgres_-_public.png
52	15	حبازة زراعية	image/png	145558	2025-11-09 23:36:49.314611+02	uploads/solidarity/15/postgres_-_public.png
53	16	بحث احتماعي	image/jpeg	23818	2025-11-09 23:46:04.398061+02	uploads/solidarity/16/1.jpg
54	16	اثبات دخل	image/jpeg	14318	2025-11-09 23:46:04.405016+02	uploads/solidarity/16/2.jpg
55	16	ص.ب ولي امر	image/png	10998	2025-11-09 23:46:04.406192+02	uploads/solidarity/16/3.png
56	16	ص.ب شخصية	image/jpeg	7046	2025-11-09 23:46:04.407462+02	uploads/solidarity/16/4.jpg
57	16	حبازة زراعية	image/png	145558	2025-11-09 23:46:04.409838+02	uploads/solidarity/16/postgres_-_public.png
58	17	بحث احتماعي	image/jpeg	23818	2025-11-10 03:36:29.752539+02	uploads/solidarity/17/1.jpg
59	17	اثبات دخل	image/jpeg	14318	2025-11-10 03:36:29.755902+02	uploads/solidarity/17/2.jpg
60	17	ص.ب ولي امر	image/jpeg	23818	2025-11-10 03:36:29.75754+02	uploads/solidarity/17/1_ziCDGz3.jpg
61	17	ص.ب شخصية	image/png	10998	2025-11-10 03:36:29.759617+02	uploads/solidarity/17/3.png
62	17	حبازة زراعية	image/png	145558	2025-11-10 03:36:29.761375+02	uploads/solidarity/17/postgres_-_public.png
63	17	تكافل و كرامة	image/jpeg	7046	2025-11-10 03:36:29.763004+02	uploads/solidarity/17/4.jpg
64	18	بحث احتماعي	image/jpeg	23818	2025-11-14 16:37:31.225708+02	uploads/solidarity/18/1.jpg
65	18	اثبات دخل	image/jpeg	14318	2025-11-14 16:37:31.230888+02	uploads/solidarity/18/2.jpg
66	24	بحث احتماعي	image/jpeg	14318	2025-11-18 21:34:50.220486+02	uploads/solidarity/24/2.jpg
67	24	اثبات دخل	image/jpeg	23818	2025-11-18 21:34:50.22459+02	uploads/solidarity/24/1.jpg
68	24	ص.ب ولي امر	image/jpeg	7046	2025-11-18 21:34:50.225951+02	uploads/solidarity/24/4.jpg
69	24	ص.ب شخصية	image/png	10998	2025-11-18 21:34:50.227059+02	uploads/solidarity/24/3.png
70	24	حبازة زراعية	image/png	145558	2025-11-18 21:34:50.233184+02	uploads/solidarity/24/postgres_-_public.png
71	25	بحث احتماعي	image/jpeg	14318	2025-11-22 01:14:55.500703+02	uploads/solidarity/25/2.jpg
72	25	اثبات دخل	image/png	10998	2025-11-22 01:14:55.503721+02	uploads/solidarity/25/3.png
73	25	ص.ب ولي امر	image/jpeg	7046	2025-11-22 01:14:55.505169+02	uploads/solidarity/25/4.jpg
74	25	ص.ب شخصية	image/jpeg	23818	2025-11-22 01:14:55.506661+02	uploads/solidarity/25/1.jpg
75	25	حبازة زراعية	image/png	10998	2025-11-22 01:14:55.507941+02	uploads/solidarity/25/3_3SWu505.png
76	26	بحث احتماعي	image/jpeg	14318	2025-11-22 16:53:59.751426+02	uploads/solidarity/26/2.jpg
77	26	اثبات دخل	image/png	10998	2025-11-22 16:53:59.755206+02	uploads/solidarity/26/3.png
78	26	ص.ب ولي امر	image/jpeg	7046	2025-11-22 16:53:59.756724+02	uploads/solidarity/26/4.jpg
79	26	ص.ب شخصية	image/png	145558	2025-11-22 16:53:59.758376+02	uploads/solidarity/26/postgres_-_public.png
80	26	حبازة زراعية	image/jpeg	23818	2025-11-22 16:53:59.760179+02	uploads/solidarity/26/1.jpg
81	27	بحث احتماعي	image/jpeg	23818	2025-11-22 20:38:22.992859+02	uploads/solidarity/27/1.jpg
82	27	اثبات دخل	image/jpeg	14318	2025-11-22 20:38:22.996678+02	uploads/solidarity/27/2.jpg
83	27	ص.ب ولي امر	image/png	10998	2025-11-22 20:38:22.997893+02	uploads/solidarity/27/3.png
84	27	ص.ب شخصية	image/jpeg	7046	2025-11-22 20:38:22.998862+02	uploads/solidarity/27/4.jpg
85	28	بحث احتماعي	image/jpeg	23818	2025-11-22 21:25:05.522867+02	uploads/solidarity/28/1.jpg
86	28	اثبات دخل	image/jpeg	14318	2025-11-22 21:25:05.525354+02	uploads/solidarity/28/2.jpg
87	28	ص.ب ولي امر	image/png	10998	2025-11-22 21:25:05.526434+02	uploads/solidarity/28/3.png
88	28	ص.ب شخصية	image/jpeg	7046	2025-11-22 21:25:05.527432+02	uploads/solidarity/28/4.jpg
89	29	بحث احتماعي	image/jpeg	23818	2025-11-22 22:07:32.063066+02	uploads/solidarity/29/1.jpg
90	29	اثبات دخل	image/jpeg	14318	2025-11-22 22:07:32.06584+02	uploads/solidarity/29/2.jpg
91	29	ص.ب ولي امر	image/png	10998	2025-11-22 22:07:32.067269+02	uploads/solidarity/29/3.png
92	29	ص.ب شخصية	image/jpeg	7046	2025-11-22 22:07:32.068566+02	uploads/solidarity/29/4.jpg
93	29	حبازة زراعية	image/png	145558	2025-11-22 22:07:32.06969+02	uploads/solidarity/29/postgres_-_public.png
94	29	تكافل و كرامة	image/png	800132	2025-11-22 22:07:32.070866+02	uploads/solidarity/29/z.png
95	30	بحث احتماعي	image/jpeg	23818	2025-11-22 22:19:25.750937+02	uploads/solidarity/30/1.jpg
96	30	اثبات دخل	image/jpeg	14318	2025-11-22 22:19:25.758465+02	uploads/solidarity/30/2.jpg
97	30	ص.ب ولي امر	image/png	10998	2025-11-22 22:19:25.75982+02	uploads/solidarity/30/3.png
98	30	ص.ب شخصية	image/jpeg	7046	2025-11-22 22:19:25.76117+02	uploads/solidarity/30/4.jpg
99	31	بحث احتماعي	image/jpeg	23818	2025-11-22 22:22:11.595803+02	uploads/solidarity/31/1.jpg
100	31	اثبات دخل	image/jpeg	14318	2025-11-22 22:22:11.598343+02	uploads/solidarity/31/2.jpg
101	31	ص.ب ولي امر	image/png	10998	2025-11-22 22:22:11.599511+02	uploads/solidarity/31/3.png
102	31	ص.ب شخصية	image/jpeg	7046	2025-11-22 22:22:11.600483+02	uploads/solidarity/31/4.jpg
103	32	بحث احتماعي	image/jpeg	23818	2025-11-22 22:23:31.138953+02	uploads/solidarity/32/1.jpg
104	32	اثبات دخل	image/jpeg	14318	2025-11-22 22:23:31.141666+02	uploads/solidarity/32/2.jpg
105	32	ص.ب ولي امر	image/png	10998	2025-11-22 22:23:31.142816+02	uploads/solidarity/32/3.png
106	32	ص.ب شخصية	image/jpeg	7046	2025-11-22 22:23:31.14387+02	uploads/solidarity/32/4.jpg
107	33	بحث احتماعي	image/jpeg	23818	2025-11-22 22:38:56.451823+02	uploads/solidarity/33/1.jpg
108	33	اثبات دخل	image/jpeg	14318	2025-11-22 22:38:56.454651+02	uploads/solidarity/33/2.jpg
109	33	ص.ب ولي امر	image/png	10998	2025-11-22 22:38:56.456063+02	uploads/solidarity/33/3.png
110	33	ص.ب شخصية	image/jpeg	7046	2025-11-22 22:38:56.45733+02	uploads/solidarity/33/4.jpg
111	34	بحث احتماعي	image/jpeg	23818	2025-11-22 23:59:10.160147+02	uploads/solidarity/34/1.jpg
112	34	اثبات دخل	image/jpeg	14318	2025-11-22 23:59:10.16495+02	uploads/solidarity/34/2.jpg
113	34	ص.ب ولي امر	image/png	10998	2025-11-22 23:59:10.166479+02	uploads/solidarity/34/3.png
114	34	ص.ب شخصية	image/jpeg	7046	2025-11-22 23:59:10.167488+02	uploads/solidarity/34/4.jpg
\.


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.students (student_id, name, email, password, faculty_id, profile_photo, gender, nid, uid, phone_number, address, acd_year, join_date, gpa, grade, major) FROM stdin;
2	ليلى خالد	l.khaled@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	2	\N	F	223456789	887654321	+966555555555	جدة	2025/2026	2025-09-01	\N	\N	كيمياء
1	محمد سعيد	m.saeed@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	M	123456789	987654321	+966501234567	الرياض	2025/2026	2025-09-01	\N	جيد جدا	هندسة حاسوب
11	A	AA@gmail.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	F	50248798655487	55857	20125455485	Eg	2025	2025-09-01	\N	\N	hg
13	S	S@gmail.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	F	50248798445487	57857	20125455785	Eg	2025	2025-09-01	\N	\N	hg
15	std2	std2@gmail.com	$2b$12$SngL6dkYpJ4WEPMQ2URgqOS4i4yBR1QGgHgWzJzqsmX9NawEBZhru	1	uploads/students/15/image.jpg	M	2021254587	2021245	+201254578	eg	4	2025-11-14	\N	ممتاز	sw
16	std3	std3@gmail.com	$2b$12$Fugft7.jfR0j.SYKQzEoj.YYEJUrQ5EpG1gJMEidLcHMGWkSZQua6	2	uploads/students/16/image.jpg	M	5055258	202255	+2012555	cairo	2	2025-11-14	\N	good	hw
17	std4	std4@gmail.com	$2b$12$ZXUb7ed4gWa.he7wbwiuFOCWgv5HITlD6spFMSpfi5Z3wRqt6Tzde	2	uploads/students/17/image.jpg	M	5555555	555555	202222222	eg	انتظام	2025-11-15	\N	جيد	sw
14	std1	s1@gmail.com	$2b$12$YRVhES6M.epwXXJfInQbNuOwDgIW9rHV8ODgyVUR8c3IqN2hpxKHC	2	uploads/students/14/image.jpg	M	20125888888	202251	2022222555	giza	4	2025-11-14	\N	جيد	H.w
18	std5	atd5@gmail.com	pbkdf2_sha256$1000000$sfWYqdwxjgzHDBMi0vd4Ky$Ymb1IAclnoHPYPPy8BYYbEpCguZHGHnr3VR6cLRcCPE=	2	uploads/students/18/image.jpg	M	20121545454	201215	203212154	eg	1	2025-11-18	\N	good	sw
19	std6	std5@gmail.com	$2b$12$WXE1vocFatp5QGZCnZdrpun3D7Kckrf8SF2RK4nYiO6xpFbEdhXn.	2	uploads/students/19/image.jpg	M	201215454540	2012150	2032121540	eg	1	2025-11-18	\N	good	sw
20	std10	std10@gmail.com	$2b$12$PD4cIEMPzqUx.o12xpBK7uNBUCqLlEDjitF63WblHy6tLeLrphOd2	2	uploads/students/20/image.jpg	M	2012154545404	20121504	20321215404	eg	1	2025-11-18	\N	good	sw
21	std11	std11@gmail.com	$2b$12$6gmbgzKH/sg/zFC2MbDLne.V3.bqQJatU1DVfflq46LkGUUd2WD3O	2	uploads/students/21/image.jpg	M	201215454540401	201215040011	2032121540400	eg	1	2025-11-18	\N	good	sw
22	omaromar	omaromar@gmail.com	$2b$12$NE14tF5M6Ac5JUVqx57t.eoS647kz1BtneSY0jKVEYkGwiTnVPEz6	1	uploads/students/22/image.jpg	m	20122222222	1122222	2012222222	eg	1	2025-11-22	\N	good	sw
\.


--
-- Name: admins_admin_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admins_admin_id_seq', 20, true);


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

SELECT pg_catalog.setval('public.auth_permission_id_seq', 108, true);


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

SELECT pg_catalog.setval('public.django_content_type_id_seq', 27, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 25, true);


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

SELECT pg_catalog.setval('public.faculties_faculty_id_seq', 3, true);


--
-- Name: families_family_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.families_family_id_seq', 1, true);


--
-- Name: logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.logs_log_id_seq', 276, true);


--
-- Name: solidarities_solidarity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solidarities_solidarity_id_seq', 34, true);


--
-- Name: solidarity_docs_doc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solidarity_docs_doc_id_seq', 114, true);


--
-- Name: students_student_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.students_student_id_seq', 22, true);


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
-- Name: solidarities trg_log_solidarity_pre_approval; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_log_solidarity_pre_approval AFTER UPDATE ON public.solidarities FOR EACH ROW WHEN (((old.req_status IS DISTINCT FROM new.req_status) AND (new.req_status = 'موافقة مبدئية'::public.general_status))) EXECUTE FUNCTION public.log_solidarity_pre_approval();


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

\unrestrict 4bMd84xQA5eS0yMqYHAsaaJg1120es5YZM2qQ5eIjLotMdFOsPoZdK84S8p5Qat

