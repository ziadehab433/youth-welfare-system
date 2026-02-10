--
-- PostgreSQL database dump
--

\restrict Hcop7CUbwNSQjhcDJt2N3PDcYTP9rXEz8VivpXQBnWgXCVrAgNEcyig6xPtOdRM

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
    'اخر',
    'نشاط رياضي',
    'نشاط ثقافي',
    'نشاط بيئي',
    'نشاط اجتماعي',
    'نشاط علمي',
    'نشاط خدمة عامة',
    'نشاط فني',
    'نشاط معسكرات',
    'اسر'
);


ALTER TYPE public.event_type OWNER TO postgres;

--
-- Name: family_members_roles; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.family_members_roles AS ENUM (
    'رائد',
    'نائب رائد',
    'مسؤول',
    'أمين صندوق',
    'أخ أكبر',
    'أخت كبرى',
    'أمين سر',
    'عضو منتخب',
    'أمين لجنة',
    'أمين مساعد لجنة',
    'عضو'
);


ALTER TYPE public.family_members_roles OWNER TO postgres;

--
-- Name: family_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.family_type AS ENUM (
    'نوعية',
    'مركزية',
    'اصدقاء البيئة'
);


ALTER TYPE public.family_type OWNER TO postgres;

--
-- Name: general_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.general_status AS ENUM (
    'موافقة مبدئية',
    'مقبول',
    'منتظر',
    'مرفوض',
    'قادم'
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
    'اخر',
    'طالب'
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
    dept_fac_ls text[] DEFAULT '{}'::text[],
    nid character varying(14),
    phone_number character varying(14),
    CONSTRAINT check_nid_format CHECK (((nid IS NULL) OR ((nid)::text ~ '^\d{14}$'::text))),
    CONSTRAINT check_phone_format CHECK (((phone_number IS NULL) OR ((phone_number)::text ~ '^\d{6,14}$'::text)))
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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    for_env_fam boolean DEFAULT false NOT NULL
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
    family_id integer,
    resource character varying(100),
    selected_facs integer[],
    plan_id integer,
    active boolean DEFAULT true,
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
    updated_at timestamp with time zone DEFAULT now(),
    min_limit integer DEFAULT 50 NOT NULL,
    type public.family_type NOT NULL,
    closing_date date
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
-- Name: family_admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.family_admins (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    nid bigint NOT NULL,
    ph_no bigint NOT NULL,
    role public.family_members_roles NOT NULL,
    family_id bigint NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.family_admins OWNER TO postgres;

--
-- Name: family_admins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.family_admins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.family_admins_id_seq OWNER TO postgres;

--
-- Name: family_admins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.family_admins_id_seq OWNED BY public.family_admins.id;


--
-- Name: family_members; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.family_members (
    family_id integer NOT NULL,
    student_id integer NOT NULL,
    role public.family_members_roles,
    status public.general_status DEFAULT 'منتظر'::public.general_status,
    joined_at timestamp with time zone DEFAULT now(),
    dept_id integer
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
    student_id integer,
    CONSTRAINT logs_single_target_check CHECK ((((target_type = 'نشاط'::public.target_type) AND (event_id IS NOT NULL) AND (solidarity_id IS NULL) AND (family_id IS NULL) AND (student_id IS NULL)) OR ((target_type = 'تكافل'::public.target_type) AND (solidarity_id IS NOT NULL) AND (event_id IS NULL) AND (family_id IS NULL) AND (student_id IS NULL)) OR ((target_type = 'اسر'::public.target_type) AND (family_id IS NOT NULL) AND (event_id IS NULL) AND (solidarity_id IS NULL) AND (student_id IS NULL)) OR ((target_type = 'طالب'::public.target_type) AND (student_id IS NOT NULL) AND (event_id IS NULL) AND (solidarity_id IS NULL))))
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
-- Name: plans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plans (
    plan_id integer NOT NULL,
    name character varying(150) NOT NULL,
    term integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    faculty_id integer
);


ALTER TABLE public.plans OWNER TO postgres;

--
-- Name: plans_plan_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.plans ALTER COLUMN plan_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.plans_plan_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.posts (
    post_id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    family_id integer NOT NULL,
    faculty_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.posts OWNER TO postgres;

--
-- Name: posts_post_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.posts_post_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.posts_post_id_seq OWNER TO postgres;

--
-- Name: posts_post_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.posts_post_id_seq OWNED BY public.posts.post_id;


--
-- Name: prtcps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prtcps (
    event_id integer NOT NULL,
    student_id integer NOT NULL,
    rank integer,
    reward character varying(255),
    status public.general_status DEFAULT 'منتظر'::public.general_status,
    id bigint NOT NULL
);


ALTER TABLE public.prtcps OWNER TO postgres;

--
-- Name: prtcps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.prtcps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.prtcps_id_seq OWNER TO postgres;

--
-- Name: prtcps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.prtcps_id_seq OWNED BY public.prtcps.id;


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
    google_id character varying(255),
    google_picture character varying(500),
    is_google_auth boolean DEFAULT false,
    auth_method character varying(20) DEFAULT 'email'::character varying,
    last_login_method character varying(20),
    last_google_login timestamp without time zone,
    can_create_fam boolean DEFAULT false NOT NULL
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
-- Name: family_admins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.family_admins ALTER COLUMN id SET DEFAULT nextval('public.family_admins_id_seq'::regclass);


--
-- Name: posts post_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts ALTER COLUMN post_id SET DEFAULT nextval('public.posts_post_id_seq'::regclass);


--
-- Name: prtcps id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prtcps ALTER COLUMN id SET DEFAULT nextval('public.prtcps_id_seq'::regclass);


--
-- Name: solidarity_docs doc_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solidarity_docs ALTER COLUMN doc_id SET DEFAULT nextval('public.solidarity_docs_doc_id_seq'::regclass);


--
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admins (admin_id, name, email, password, faculty_id, dept_id, created_at, can_create, can_update, can_read, can_delete, acc_status, role, dept_fac_ls, nid, phone_number) FROM stdin;
8	omar	omar@gmail.com	pbkdf2_sha256$1000000$vlZHhPpW9IpNAdiVAlRLoZ$EKZZMi53hEdx/k1aLRSkqXWKnmZgVcXUMN0N8tP7RNQ=	1	\N	2025-10-30 01:10:42.356929+03	t	t	t	t	active	مسؤول كلية	{string,"فني و ثقافي"}	\N	\N
4	سارة محمد	sara.head@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير كلية	{}	\N	\N
12	string	user@example.com	pbkdf2_sha256$1000000$IrRY86mbOwprrogP9aOI2H$2RgAvUXSAwxSeNHNhdSuu+RXGdAhwr9bghYxx5mvfZY=	1	\N	2025-11-15 03:13:03.29534+02	t	t	t	t	active	مسؤول كلية	{}	\N	\N
16	oo	oo@gmail.com	pbkdf2_sha256$1000000$QXXplajwQLlKBLRkvWyEDG$j2Hy8tqFThcTmWs+C0g6pFfGvVtrklz/leeYU9X0WzI=	\N	\N	2025-11-18 20:45:57.231286+02	t	t	t	t	active	مدير ادارة	{تكافل}	\N	\N
6	منى يوسف	mona.general@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير عام	{}	\N	\N
13	string	admin@example.com	pbkdf2_sha256$1000000$QvWcdHW5PZf3birfhgr1K1$ze8CXVUv+iOXUkR+zOGt0dx9HGx9I5Tsl47DoOmL4KY=	\N	\N	2025-11-15 03:30:33.532263+02	t	t	t	t	string	مشرف النظام	{}	\N	\N
14	a4	ar@gmail.com.com	pbkdf2_sha256$1000000$zBktzHX9eDrOqSc9VSreRz$eFZqgCmqCYdzJ7TUfKZQoUaOXXPxgicfH1cyjNL31dQ=	\N	\N	2025-11-15 03:36:53.711315+02	t	t	t	t	active	مشرف النظام	{}	\N	\N
15	ali	alioamar@gmail.com	pbkdf2_sha256$1000000$MYace5Oq8w4z1fOtwxrC3A$d8Vh8UhpL/6nKz4RcdwtRDIWAoso5ZxHTELq+wOJfMs=	1	\N	2025-11-18 20:27:49.844806+02	t	t	t	t	active	مسؤول كلية	{"نشاط فني","نشاط رياضي"}	\N	\N
17	aa	aa@gmail.com	pbkdf2_sha256$1000000$2dc1qpkT0K2Rvf8jYCZFGr$RYI8fid0TOn0KPMmVGLXDSb+4fCh2gtoN+F/KrCJ0RE=	2	\N	2025-11-18 21:42:50.130782+02	t	t	t	t	active	مسؤول كلية	{"نشاط فمي",تكافل}	\N	\N
5	خالد إبراهيم	khaled.manager@example.com	pbkdf2_sha256$1000000$6rS7AFWRCbRmGf2v87CR0Q$XLigYMDMnB9E0MwVlDgY1YZcxbM3wADe3VuYh1mGxSM=	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير ادارة	{}	\N	\N
21	ahmed	ahmedm@gmail.com	pbkdf2_sha256$1000000$St8cjm17fUYZx0iDOZwRy0$8HFztv938EE0udu8cAekPGKmbFDVRfrWClNO6R1xEfc=	\N	\N	2025-12-09 23:28:44.320432+02	t	t	t	t	active	مشرف النظام	{string}	99739715871769	2012222222
18	admin12	admin12@gmail.com	pbkdf2_sha256$1000000$sZ9BCWoeUQKBmW1h4mY3g8$QqXoHVTnnHG6Xtk3BeqX21BCFPeh1zN6RD1cWtz/Ads=	2	\N	2025-11-18 23:03:16.0987+02	t	t	t	t	نشط	مسؤول كلية	{"فني و رياضي",رياضي}	\N	\N
1	ahmed	ahmed@gmail.com	pbkdf2_sha256$1000000$dx0GL2Uj1qVCDZa7x83045$0q9vmyfE+Bf0237qGzyUVvtqnJEauuW6eauxJra+CIM=	1	\N	2025-10-20 02:34:30.31113+03	t	t	t	t	active	مسؤول كلية	{"نشاط فني و ثقافي"}	\N	\N
3	أحمد علي	ahmed.faculty@example.com	pbkdf2_sha256$1000000$k0IQx82TzGMhVAFEe6Y8Zl$oiR9QGJQIceP5VudDGMnLBdeXYfJPbgW1rmeNzobO0g=	3	\N	2025-10-20 02:53:23.217139+03	t	t	t	f	active	مسؤول كلية	{}	\N	\N
19	admin33	admin33@example.com	pbkdf2_sha256$1000000$rEqE9UmuMQqskvYGjne6Nd$T0ST6Ew8rabU2sFpgL/o90T4uhB8PUvkNCzOOOYIUI4=	2	\N	2025-11-21 16:33:42.63292+02	t	t	t	t	active	مسؤول كلية	{فني,رياضي}	\N	\N
20	admin34	admin34@example.com	pbkdf2_sha256$1000000$WqUSKaWUHuPX89VGicr9jA$La3PHY+349r/DeTyaXSvAoO3K3S5JvzcI/I7rq2ltVk=	2	\N	2025-11-21 16:34:27.807083+02	t	t	t	t	active	مسؤول كلية	{فني,رياضي,ثقافي}	\N	\N
7	محمد سعيد	mohamed.super@example.com	pbkdf2_sha256$1000000$yOdSWDrX15vKLosN6Dp41Y$I5NAsjlV29vxASgyoBCPnikiCcl9wf9fPvCxXSHt4Ys=	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مشرف النظام	{}	\N	\N
9	ali	ali@gmail.com	pbkdf2_sha256$1000000$g5LSEHFQAOV5imJXliaDcS$EC34z7cDVSgQjTbt3313xwvXrj72TCS+GExZENNjMI4=	1	\N	2025-10-30 01:34:00.847159+03	t	t	t	t	active	مسؤول كلية	{"فني و ثقافي",رياضي}	\N	\N
11	B	B@gmail.com	pbkdf2_sha256$1000000$wrgC5ZDwinGSr1g0SR8vrz$RZ3Xy50cG9qhkw+toLxLTBdGpMndW5G/SgY3Iewb9EE=	\N	\N	2025-10-30 02:09:47.364118+03	t	t	t	t	active	مشرف النظام	{}	\N	\N
10	A	A@gmail.com	pbkdf2_sha256$1000000$wN2OdjwYyuKZ9kKEjKkhPH$LMzBhFiIGlM6QlllHD9z+PtdJd1aF0hNRQdCTFJgYRY=	\N	\N	2025-10-30 01:37:07.429515+03	t	t	t	t	active	مشرف النظام	{}	\N	\N
2	سارة محمد	sara@example.com	pbkdf2_sha256$1000000$YOum6XQm4YPTyOygoretCH$qI6iJdP+RHVI5jCneq2CYhb88PnvNhsdvduSklDyMaI=	2	\N	2025-10-20 02:34:30.31113+03	t	t	t	f	active	مسؤول كلية	{"فني و ثقافي"}	\N	\N
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

COPY public.departments (dept_id, name, description, created_at, for_env_fam) FROM stdin;
3	الأنشطة الرياضية	قسم الأنشطة والفعاليات الرياضية	2025-11-29 18:30:35.253433+02	f
4	الأنشطة الثقافية	قسم الأنشطة الثقافية والفنية	2025-11-29 18:30:35.253433+02	f
5	الأنشطة البيئية	قسم الأنشطة البيئية والاستدامة	2025-11-29 18:30:35.253433+02	t
6	الأنشطة الاجتماعية	قسم الأنشطة الاجتماعية والخدمة المجتمعية	2025-11-29 18:30:35.253433+02	f
7	الأنشطة العلمية	قسم الأنشطة العلمية والبحثية	2025-11-29 18:30:35.253433+02	f
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
\.


--
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.events (event_id, title, description, dept_id, faculty_id, created_by, updated_at, cost, location, restrictions, reward, status, imgs, st_date, end_date, s_limit, created_at, type, family_id, resource, selected_facs, plan_id, active) FROM stdin;
4	مسابقة الخطابة والإلقاء	مسابقة لاختبار مهارات الخطابة والإلقاء لدى الطلاب	4	2	1	2025-11-29 18:47:41.600095+02	30.00	الحاضرة الكبرى	يجب أن يكون المشارك متقنًا للغة العربية	جوائز نقدية وشهادات دولية	منتظر	\N	2024-04-05	2024-04-07	120	2025-11-29 18:47:41.600095+02	نشاط ثقافي	1	\N	\N	\N	t
5	يوم التطوع الاجتماعي	فعالية تطوعية للمساهمة في الخدمة المجتمعية والنشاطات الاجتماعية	6	1	1	2025-12-07 16:53:23.406092+02	0.00	مراكز الخدمة الاجتماعية	لا توجد قيود	شهادات تطوع معترف بها	مقبول	\N	2024-03-25	2024-03-26	250	2025-11-29 18:47:41.600095+02	نشاط اجتماعي	2	\N	\N	\N	t
7	ندوة البحث العلمي	ندوة علمية لمناقشة أحدث الأبحاث العلمية في المجالات المختلفة	5	3	1	2025-12-07 16:53:23.406092+02	25.00	قاعة المؤتمرات	يفضل أن يكون المشارك من طلاب الدراسات العليا	شهادات حضور وفرص تعاون بحثي	مقبول	\N	2024-05-01	2024-05-02	80	2025-11-29 18:47:41.600095+02	نشاط علمي	2	\N	\N	\N	t
8	بطولة كرة القدم الثلاثية	بطولة رياضية لكرة القدم تجمع بين فرق من مختلف الكليات	3	1	1	2025-12-07 16:53:23.406092+02	40.00	ملعب كرة القدم	يجب أن تكون الفرق من طلاب الجامعة فقط	كأس ودروع تذكارية وشهادات	مقبول	\N	2024-04-20	2024-04-25	180	2025-11-29 18:47:41.600095+02	نشاط رياضي	2	\N	\N	\N	t
10	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:16:53.936213+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:16:53.936244+02	نشاط ثقافي	4	\N	\N	\N	t
11	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:18:45.66422+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:18:45.664251+02	نشاط ثقافي	4	\N	\N	\N	t
12	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:19:10.52061+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:19:10.520637+02	نشاط ثقافي	4	\N	\N	\N	t
13	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:19:12.852796+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:19:12.85282+02	نشاط ثقافي	4	\N	\N	\N	t
14	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:19:44.659524+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:19:44.659554+02	نشاط ثقافي	4	\N	\N	\N	t
15	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:20:41.032704+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:20:41.032732+02	نشاط ثقافي	4	\N	\N	\N	t
16	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:21:03.009015+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:21:03.009047+02	نشاط ثقافي	4	\N	\N	\N	t
17	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:44:36.565793+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:44:36.565822+02	نشاط ثقافي	4	\N	\N	\N	t
18	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:45:35.736096+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:45:35.736127+02	نشاط ثقافي	4	\N	\N	\N	t
19	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:47:51.603418+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:47:51.603447+02	نشاط ثقافي	4	\N	\N	\N	t
20	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:48:38.107583+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:48:38.107613+02	نشاط ثقافي	4	\N	\N	\N	t
21	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:59:21.060944+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 17:59:21.060974+02	نشاط ثقافي	4	\N	\N	\N	t
22	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:00:28.202776+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:00:28.202806+02	نشاط ثقافي	4	\N	\N	\N	t
23	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:01:34.368368+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:01:34.368398+02	نشاط ثقافي	4	\N	\N	\N	t
24	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:05:37.287877+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:05:37.287907+02	نشاط ثقافي	4	\N	\N	\N	t
25	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:07:47.105303+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:07:47.105327+02	نشاط ثقافي	4	\N	\N	\N	t
26	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:10:20.311338+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:10:20.31137+02	نشاط ثقافي	4	\N	\N	\N	t
27	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:12:30.503864+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:12:30.503894+02	نشاط ثقافي	4	\N	\N	\N	t
28	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:19:58.057411+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:19:58.057439+02	نشاط ثقافي	4	\N	\N	\N	t
29	مسابقة دينية	مسابقة حفظ القران الكريم	4	1	1	2025-12-07 18:21:19.632783+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:21:19.632811+02	نشاط ثقافي	4	\N	\N	\N	t
30	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:25:56.956089+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	\N	2025-12-07	2025-12-07	100	2025-12-07 18:25:56.956135+02	نشاط ثقافي	4	\N	\N	\N	t
31	ندوة ثقافية حول الأدب العربي	ندوة متخصصة تناقش أهم التطورات في الأدب العربي الحديث	3	1	1	2025-12-11 23:30:45.939572+02	500.00	قاعة المحاضرات الرئيسية	\N	\N	منتظر	\N	2024-03-15	2024-03-15	\N	2025-12-11 23:30:45.939607+02	\N	19	\N	\N	\N	t
32	معرض الفنون الشعبية	عرض للفنون الشعبية التقليدية	3	1	1	2025-12-11 23:30:45.945499+02	1000.00	مركز الفنون	\N	\N	منتظر	\N	2024-04-01	2024-04-03	\N	2025-12-11 23:30:45.945529+02	\N	19	\N	\N	\N	t
33	ورشة تصميم الملصقات	تدريب على تصميم ملصقات جذابة	4	1	1	2025-12-11 23:30:45.948302+02	300.00	قاعة التصميم	\N	\N	منتظر	\N	2024-03-20	2024-03-20	\N	2025-12-11 23:30:45.948323+02	\N	19	\N	\N	\N	t
34	رحلة ترفيهية إلى الطبيعة	رحلة جماعية للاستمتاع بالطبيعة	5	1	1	2025-12-11 23:30:45.950799+02	2000.00	محمية الطبيعة	\N	\N	منتظر	\N	2024-04-10	2024-04-10	\N	2025-12-11 23:30:45.950819+02	\N	19	\N	\N	\N	t
9	مسابقة فنية	مسابقة للانشطة الفنية	\N	\N	5	2025-12-14 18:04:11.160868+02	\N	مصر		شهادة تقدير	مقبول	\N	2025-12-07	2025-12-07	10	2025-12-07 16:56:05.82235+02	نشاط فني	2	\N	\N	\N	t
6	حملة البيئة النظيفة	حملة تطوعية للحفاظ على نظافة الحرم الجامعي والبيئة المحيطة	5	1	1	2026-01-21 17:53:06.516454+02	0.00	الحرم الجامعي	يفضل المشاركة في الأنشطة البيئية السابقة	شهادات تطوع وجوائز رمزية	مقبول	\N	2024-03-20	2027-03-21	100	2025-11-29 18:47:41.600095+02	نشاط بيئي	3	\N	\N	\N	t
35	ورشة الرسم الحديث	تعليم تقنيات الرسم الحديثة والفن المعاصر	6	1	1	2025-12-11 23:30:45.953555+02	600.00	معهد الفنون	\N	\N	منتظر	\N	2024-03-25	2024-03-25	\N	2025-12-11 23:30:45.953575+02	\N	19	\N	\N	\N	t
36	محاضرة علمية عن الذكاء الاصطناعي	محاضرة عن تطبيقات الذكاء الاصطناعي في العالم الحقيقي	7	1	1	2025-12-11 23:30:45.956888+02	800.00	مختبر العلوم	\N	\N	منتظر	\N	2024-05-01	2024-05-01	\N	2025-12-11 23:30:45.956916+02	\N	19	\N	\N	\N	t
37	حملة تنظيف المجتمع	حملة تطوعية لتنظيف أماكن بيئية حساسة	3	1	1	2025-12-11 23:30:45.960643+02	400.00	الحي السكني	\N	\N	منتظر	\N	2024-04-20	2024-04-20	\N	2025-12-11 23:30:45.960667+02	\N	19	\N	\N	\N	t
38	بطولة كرة القدم الودية	بطولة ودية بين أسر الجامعة	4	1	1	2025-12-11 23:30:45.964038+02	1500.00	الملعب الرياضي	\N	\N	منتظر	\N	2024-05-15	2024-05-20	\N	2025-12-11 23:30:45.96406+02	\N	19	\N	\N	\N	t
39	ندوة ثقافية حول الأدب العربي	ندوة متخصصة تناقش أهم التطورات في الأدب العربي الحديث	3	1	1	2025-12-11 23:34:26.184696+02	500.00	قاعة المحاضرات الرئيسية	\N	\N	منتظر	\N	2024-03-15	2024-03-15	\N	2025-12-11 23:34:26.184728+02	اسر	20	\N	\N	\N	t
40	معرض الفنون الشعبية	عرض للفنون الشعبية التقليدية	3	1	1	2025-12-11 23:34:26.1873+02	1000.00	مركز الفنون	\N	\N	منتظر	\N	2024-04-01	2024-04-03	\N	2025-12-11 23:34:26.187325+02	اسر	20	\N	\N	\N	t
41	ورشة تصميم الملصقات	تدريب على تصميم ملصقات جذابة	4	1	1	2025-12-11 23:34:26.189927+02	300.00	قاعة التصميم	\N	\N	منتظر	\N	2024-03-20	2024-03-20	\N	2025-12-11 23:34:26.189949+02	اسر	20	\N	\N	\N	t
42	رحلة ترفيهية إلى الطبيعة	رحلة جماعية للاستمتاع بالطبيعة	5	1	1	2025-12-11 23:34:26.192812+02	2000.00	محمية الطبيعة	\N	\N	منتظر	\N	2024-04-10	2024-04-10	\N	2025-12-11 23:34:26.192836+02	اسر	20	\N	\N	\N	t
43	ورشة الرسم الحديث	تعليم تقنيات الرسم الحديثة والفن المعاصر	6	1	1	2025-12-11 23:34:26.195749+02	600.00	معهد الفنون	\N	\N	منتظر	\N	2024-03-25	2024-03-25	\N	2025-12-11 23:34:26.195776+02	اسر	20	\N	\N	\N	t
44	محاضرة علمية عن الذكاء الاصطناعي	محاضرة عن تطبيقات الذكاء الاصطناعي في العالم الحقيقي	7	1	1	2025-12-11 23:34:26.198632+02	800.00	مختبر العلوم	\N	\N	منتظر	\N	2024-05-01	2024-05-01	\N	2025-12-11 23:34:26.198655+02	اسر	20	\N	\N	\N	t
45	حملة تنظيف المجتمع	حملة تطوعية لتنظيف أماكن بيئية حساسة	3	1	1	2025-12-11 23:34:26.201236+02	400.00	الحي السكني	\N	\N	منتظر	\N	2024-04-20	2024-04-20	\N	2025-12-11 23:34:26.201259+02	اسر	20	\N	\N	\N	t
46	بطولة كرة القدم الودية	بطولة ودية بين أسر الجامعة	4	1	1	2025-12-11 23:34:26.203541+02	1500.00	الملعب الرياضي	\N	\N	منتظر	\N	2024-05-15	2024-05-20	\N	2025-12-11 23:34:26.203563+02	اسر	20	\N	\N	\N	t
47	ندوة ثقافية حول الأدب العربي	ندوة متخصصة تناقش أهم التطورات في الأدب العربي الحديث	3	1	1	2025-12-12 00:55:32.047353+02	500.00	قاعة المحاضرات الرئيسية	\N	\N	منتظر	\N	2024-03-15	2024-03-15	\N	2025-12-12 00:55:32.047388+02	اسر	21	\N	\N	\N	t
48	معرض الفنون الشعبية	عرض للفنون الشعبية التقليدية	3	1	1	2025-12-12 00:55:32.052451+02	1000.00	مركز الفنون	\N	\N	منتظر	\N	2024-04-01	2024-04-03	\N	2025-12-12 00:55:32.052484+02	اسر	21	\N	\N	\N	t
49	ورشة تصميم الملصقات	تدريب على تصميم ملصقات جذابة	4	1	1	2025-12-12 00:55:32.057435+02	300.00	قاعة التصميم	\N	\N	منتظر	\N	2024-03-20	2024-03-20	\N	2025-12-12 00:55:32.057477+02	اسر	21	\N	\N	\N	t
50	رحلة ترفيهية إلى الطبيعة	رحلة جماعية للاستمتاع بالطبيعة	5	1	1	2025-12-12 00:55:32.061776+02	2000.00	محمية الطبيعة	\N	\N	منتظر	\N	2024-04-10	2024-04-10	\N	2025-12-12 00:55:32.061811+02	اسر	21	\N	\N	\N	t
51	ورشة الرسم الحديث	تعليم تقنيات الرسم الحديثة والفن المعاصر	6	1	1	2025-12-12 00:55:32.065436+02	600.00	معهد الفنون	\N	\N	منتظر	\N	2024-03-25	2024-03-25	\N	2025-12-12 00:55:32.065461+02	اسر	21	\N	\N	\N	t
52	محاضرة علمية عن الذكاء الاصطناعي	محاضرة عن تطبيقات الذكاء الاصطناعي في العالم الحقيقي	7	1	1	2025-12-12 00:55:32.06883+02	800.00	مختبر العلوم	\N	\N	منتظر	\N	2024-05-01	2024-05-01	\N	2025-12-12 00:55:32.068857+02	اسر	21	\N	\N	\N	t
53	حملة تنظيف المجتمع	حملة تطوعية لتنظيف أماكن بيئية حساسة	3	1	1	2025-12-12 00:55:32.07342+02	400.00	الحي السكني	\N	\N	منتظر	\N	2024-04-20	2024-04-20	\N	2025-12-12 00:55:32.073447+02	اسر	21	\N	\N	\N	t
54	بطولة كرة القدم الودية	بطولة ودية بين أسر الجامعة	4	1	1	2025-12-12 00:55:32.078057+02	1500.00	الملعب الرياضي	\N	\N	منتظر	\N	2024-05-15	2024-05-20	\N	2025-12-12 00:55:32.078086+02	اسر	21	\N	\N	\N	t
55	مسابقة	مسابقة فنية	5	1	1	2025-12-12 02:11:20.194925+02	\N	مسرح			منتظر	\N	2025-12-12	2025-12-12	100	2025-12-12 02:11:20.194955+02	نشاط فني	21	\N	\N	\N	t
3	ماراثون العدو السنوي	فعالية رياضية سنوية تجمع طلاب الجامعة للمشاركة في ماراثون العدو	3	1	1	2026-01-19 03:37:26.642264+02	50.00	الملعب الرياضي	يجب أن يكون المشارك طالباً حالياً بالجامعة	جوائز نقدية وشهادات تقدير	مقبول	\N	2024-03-15	2026-03-30	200	2025-11-29 18:47:41.600095+02	نشاط رياضي	1	\N	\N	\N	t
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

COPY public.families (family_id, name, description, faculty_id, created_by, approved_by, status, created_at, updated_at, min_limit, type, closing_date) FROM stdin;
3	أصدقاء البيئة	أسرة متخصصة في الأنشطة البيئية والاستدامة	1	1	16	موافقة مبدئية	2025-11-29 18:30:42.982008+02	2026-01-20 16:31:59.267622+02	30	اصدقاء البيئة	2025-01-01
4	نادي الرياضة	أسرة متخصصة في الأنشطة الرياضية والنشاط البدني	1	1	\N	مرفوض	2025-12-06 23:12:48.322738+02	2025-12-14 17:44:27.358042+02	50	نوعية	2025-01-01
2	أسرة مركزية	أسرة مركزية على مستوى الجامعة غير مرتبطة بكلية معينة	1	1	10	مقبول	2025-11-29 18:30:42.982008+02	2026-01-17 00:10:47.449816+02	100	مركزية	2025-01-01
1	أسرة نوعية	أسرة نوعية متخصصة في الأنشطة الرياضية والثقافية	1	1	1	مقبول	2025-11-29 18:30:42.982008+02	2026-01-19 03:31:33.578567+02	100	نوعية	2025-12-14
5	نادي الرياضة	أسرة متخصصة في الأنشطة الرياضية والنشاط البدني	1	1	\N	موافقة مبدئية	2025-12-06 23:22:21.065725+02	2025-12-12 21:21:53.420012+02	50	نوعية	2025-01-01
6	نادي الرياضة	أسرة متخصصة في الأنشطة الرياضية والنشاط البدني	1	1	\N	موافقة مبدئية	2025-12-06 23:30:14.220471+02	2025-12-12 21:21:53.420012+02	15	نوعية	2025-01-01
14	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-11 23:13:26.605204+02	2025-12-12 21:21:53.420012+02	20	نوعية	\N
16	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-11 23:16:04.293144+02	2025-12-12 21:21:53.420012+02	20	نوعية	\N
19	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-11 23:30:45.911519+02	2025-12-12 21:21:53.420012+02	20	نوعية	\N
20	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-11 23:34:26.155704+02	2025-12-12 21:21:53.420012+02	20	نوعية	\N
21	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-12 00:55:32.002298+02	2025-12-12 21:21:53.420012+02	15	نوعية	\N
\.


--
-- Data for Name: family_admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.family_admins (id, name, nid, ph_no, role, family_id, created_at) FROM stdin;
29	د. أحمد محمد علي	1234567890123	966501234567	رائد	14	2025-12-11 21:13:26.604682
30	د. فاطمة خالد	9876543210987	966569876543	نائب رائد	14	2025-12-11 21:13:26.604682
31	أ. محمود سالم	5555555555555	966505555555	مسؤول	14	2025-12-11 21:13:26.604682
32	أ. سارة يوسف	3333333333333	966503333333	أمين صندوق	14	2025-12-11 21:13:26.604682
37	د. أحمد محمد علي	1234567890123	966501234567	رائد	16	2025-12-11 21:16:04.292656
38	د. فاطمة خالد	9876543210987	966569876543	نائب رائد	16	2025-12-11 21:16:04.292656
39	أ. محمود سالم	5555555555555	966505555555	مسؤول	16	2025-12-11 21:16:04.292656
40	أ. سارة يوسف	3333333333333	966503333333	أمين صندوق	16	2025-12-11 21:16:04.292656
49	د. أحمد محمد علي	1234567890123	966501234567	رائد	19	2025-12-11 21:30:45.910745
50	د. فاطمة خالد	9876543210987	966569876543	نائب رائد	19	2025-12-11 21:30:45.910745
51	أ. محمود سالم	5555555555555	966505555555	مسؤول	19	2025-12-11 21:30:45.910745
52	أ. سارة يوسف	3333333333333	966503333333	أمين صندوق	19	2025-12-11 21:30:45.910745
53	د. أحمد محمد علي	1234567890123	966501234567	رائد	20	2025-12-11 21:34:26.155201
54	د. فاطمة خالد	9876543210987	966569876543	نائب رائد	20	2025-12-11 21:34:26.155201
55	أ. محمود سالم	5555555555555	966505555555	مسؤول	20	2025-12-11 21:34:26.155201
56	أ. سارة يوسف	3333333333333	966503333333	أمين صندوق	20	2025-12-11 21:34:26.155201
57	د. أحمد محمد علي	1234567890123	966501234567	رائد	21	2025-12-11 22:55:32.001674
58	د. فاطمة خالد	9876543210987	966569876543	نائب رائد	21	2025-12-11 22:55:32.001674
59	أ. محمود سالم	5555555555555	966505555555	مسؤول	21	2025-12-11 22:55:32.001674
60	أ. سارة يوسف	3333333333333	966503333333	أمين صندوق	21	2025-12-11 22:55:32.001674
\.


--
-- Data for Name: family_members; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.family_members (family_id, student_id, role, status, joined_at, dept_id) FROM stdin;
3	20	أخت كبرى	مرفوض	2025-11-29 18:35:41.878043+02	5
3	22	عضو	مقبول	2025-11-29 18:35:41.878043+02	5
3	16	عضو	مقبول	2025-11-29 18:35:41.878043+02	5
3	21	عضو	موافقة مبدئية	2025-11-29 18:35:41.878043+02	5
3	11	عضو	مقبول	2025-12-06 22:42:57.139362+02	\N
2	16	أخت كبرى	منتظر	2025-11-29 18:35:41.878043+02	4
4	22	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.338154+02	3
4	34	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.338532+02	3
4	1	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.339141+02	4
4	35	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.339442+02	5
4	36	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.339764+02	5
4	28	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.340044+02	3
5	22	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.074009+02	3
5	34	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.074268+02	3
5	1	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.074852+02	4
5	35	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.075165+02	5
5	36	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.075487+02	5
5	28	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.075823+02	3
6	22	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.22938+02	3
6	34	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.229667+02	3
6	1	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.230245+02	4
6	35	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.230509+02	5
6	36	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.230768+02	5
6	28	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.231031+02	3
2	18	عضو	منتظر	2025-11-29 18:35:41.878043+02	4
2	11	عضو	منتظر	2025-11-29 18:35:41.878043+02	4
1	13	عضو	منتظر	2025-11-29 18:35:41.878043+02	3
3	19	أخ أكبر	مقبول	2025-11-29 18:35:41.878043+02	5
3	13	عضو	مقبول	2025-11-29 18:35:41.878043+02	\N
4	16	أمين لجنة	منتظر	2025-12-06 23:12:48.335907+02	3
4	18	أمين لجنة	منتظر	2025-12-06 23:12:48.336729+02	4
4	19	أمين لجنة	منتظر	2025-12-06 23:12:48.33714+02	5
4	20	أمين لجنة	منتظر	2025-12-06 23:12:48.33749+02	5
4	21	أمين لجنة	منتظر	2025-12-06 23:12:48.337833+02	3
5	16	أمين لجنة	منتظر	2025-12-06 23:22:21.072099+02	3
5	18	أمين لجنة	منتظر	2025-12-06 23:22:21.072812+02	4
5	19	أمين لجنة	منتظر	2025-12-06 23:22:21.073167+02	5
5	20	أمين لجنة	منتظر	2025-12-06 23:22:21.073458+02	5
5	21	أمين لجنة	منتظر	2025-12-06 23:22:21.073746+02	3
6	16	أمين لجنة	منتظر	2025-12-06 23:30:14.22727+02	3
6	18	أمين لجنة	منتظر	2025-12-06 23:30:14.228077+02	4
6	19	أمين لجنة	منتظر	2025-12-06 23:30:14.22845+02	5
6	20	أمين لجنة	منتظر	2025-12-06 23:30:14.228771+02	5
6	21	أمين لجنة	منتظر	2025-12-06 23:30:14.229093+02	3
1	11	أخ أكبر	منتظر	2025-11-29 18:35:41.878043+02	3
4	11	أخ أكبر	منتظر	2025-12-06 23:12:48.334231+02	\N
5	11	أخ أكبر	منتظر	2025-12-06 23:22:21.070555+02	\N
6	13	أخ أكبر	منتظر	2025-12-06 23:30:14.225358+02	\N
14	18	أخت كبرى	منتظر	2025-12-11 23:13:26.620967+02	\N
14	29	أمين سر	منتظر	2025-12-11 23:13:26.623685+02	\N
14	36	عضو منتخب	منتظر	2025-12-11 23:13:26.626447+02	\N
14	13	عضو منتخب	منتظر	2025-12-11 23:13:26.62934+02	\N
14	22	أمين لجنة	منتظر	2025-12-11 23:13:26.63106+02	3
14	1	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.631554+02	3
14	11	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.633565+02	4
14	35	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.635391+02	5
14	20	أمين لجنة	منتظر	2025-12-11 23:13:26.636874+02	6
14	21	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.637157+02	6
14	28	أمين لجنة	منتظر	2025-12-11 23:13:26.638601+02	7
14	34	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.638879+02	7
14	2	أمين لجنة	منتظر	2025-12-11 23:13:26.640341+02	3
14	16	أمين لجنة	منتظر	2025-12-11 23:13:26.642112+02	4
14	19	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.64242+02	4
16	18	أخت كبرى	منتظر	2025-12-11 23:16:04.3069+02	\N
16	29	أمين سر	منتظر	2025-12-11 23:16:04.309537+02	\N
16	36	عضو منتخب	منتظر	2025-12-11 23:16:04.31212+02	\N
16	13	عضو منتخب	منتظر	2025-12-11 23:16:04.314664+02	\N
16	22	أمين لجنة	منتظر	2025-12-11 23:16:04.316225+02	3
16	1	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.316632+02	3
16	11	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.318438+02	4
16	35	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.320193+02	5
16	20	أمين لجنة	منتظر	2025-12-11 23:16:04.321799+02	6
16	21	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.322166+02	6
16	28	أمين لجنة	منتظر	2025-12-11 23:16:04.323732+02	7
16	34	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.324023+02	7
16	2	أمين لجنة	منتظر	2025-12-11 23:16:04.325461+02	3
16	16	أمين لجنة	منتظر	2025-12-11 23:16:04.3272+02	4
16	19	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.327471+02	4
19	18	أخت كبرى	منتظر	2025-12-11 23:30:45.928583+02	\N
19	29	أمين سر	منتظر	2025-12-11 23:30:45.931432+02	\N
19	36	عضو منتخب	منتظر	2025-12-11 23:30:45.934086+02	\N
19	13	عضو منتخب	منتظر	2025-12-11 23:30:45.937087+02	\N
19	22	أمين لجنة	منتظر	2025-12-11 23:30:45.938712+02	3
19	1	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.939134+02	3
19	11	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.947971+02	4
19	35	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.950474+02	5
19	20	أمين لجنة	منتظر	2025-12-11 23:30:45.952963+02	6
19	21	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.953251+02	6
19	28	أمين لجنة	منتظر	2025-12-11 23:30:45.956106+02	7
19	34	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.956415+02	7
19	2	أمين لجنة	منتظر	2025-12-11 23:30:45.959918+02	3
19	16	أمين لجنة	منتظر	2025-12-11 23:30:45.962716+02	4
19	19	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.962996+02	4
20	18	أخت كبرى	منتظر	2025-12-11 23:34:26.172512+02	\N
20	29	أمين سر	منتظر	2025-12-11 23:34:26.175937+02	\N
20	36	عضو منتخب	منتظر	2025-12-11 23:34:26.179042+02	\N
20	13	عضو منتخب	منتظر	2025-12-11 23:34:26.182066+02	\N
20	22	أمين لجنة	منتظر	2025-12-11 23:34:26.18379+02	3
20	1	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.184247+02	3
20	11	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.189595+02	4
20	35	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.192458+02	5
20	20	أمين لجنة	منتظر	2025-12-11 23:34:26.194989+02	6
20	21	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.195347+02	6
20	28	أمين لجنة	منتظر	2025-12-11 23:34:26.197993+02	7
20	34	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.19831+02	7
20	2	أمين لجنة	منتظر	2025-12-11 23:34:26.200643+02	3
20	16	أمين لجنة	منتظر	2025-12-11 23:34:26.20295+02	4
20	19	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.203236+02	4
21	18	أخت كبرى	منتظر	2025-12-12 00:55:32.028676+02	\N
21	29	أمين سر	منتظر	2025-12-12 00:55:32.03241+02	\N
21	36	عضو منتخب	منتظر	2025-12-12 00:55:32.037065+02	\N
21	13	عضو منتخب	منتظر	2025-12-12 00:55:32.042859+02	\N
21	22	أمين لجنة	منتظر	2025-12-12 00:55:32.045295+02	3
21	1	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.046602+02	3
21	11	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.056726+02	4
21	35	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.061121+02	5
21	20	أمين لجنة	منتظر	2025-12-12 00:55:32.064671+02	6
21	21	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.065059+02	6
21	28	أمين لجنة	منتظر	2025-12-12 00:55:32.067986+02	7
21	34	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.068406+02	7
21	2	أمين لجنة	منتظر	2025-12-12 00:55:32.072529+02	3
21	16	أمين لجنة	منتظر	2025-12-12 00:55:32.076667+02	4
21	19	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.077141+02	4
\.


--
-- Data for Name: logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.logs (log_id, actor_id, action, event_id, solidarity_id, family_id, ip_address, logged_at, actor_type, target_type, student_id) FROM stdin;
1	1	انشاء اسر	\N	\N	1	::1	2025-11-29 18:30:42.982008+02	\N	اسر	\N
2	1	انشاء اسر	\N	\N	2	::1	2025-11-29 18:30:42.982008+02	\N	اسر	\N
3	1	انشاء اسر	\N	\N	3	::1	2025-11-29 18:30:42.982008+02	\N	اسر	\N
4	1	انشاء نشاط	3	\N	\N	::1	2025-11-29 18:47:41.600095+02	\N	نشاط	\N
5	1	انشاء نشاط	4	\N	\N	::1	2025-11-29 18:47:41.600095+02	\N	نشاط	\N
6	1	انشاء نشاط	5	\N	\N	::1	2025-11-29 18:47:41.600095+02	\N	نشاط	\N
7	1	انشاء نشاط	6	\N	\N	::1	2025-11-29 18:47:41.600095+02	\N	نشاط	\N
8	1	انشاء نشاط	7	\N	\N	::1	2025-11-29 18:47:41.600095+02	\N	نشاط	\N
9	1	انشاء نشاط	8	\N	\N	::1	2025-11-29 18:47:41.600095+02	\N	نشاط	\N
11	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:26.846068+02	مسؤول كلية	تكافل	\N
10	8	عرض بيانات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:26.845212+02	مسؤول كلية	تكافل	\N
12	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:26.911681+02	مسؤول كلية	تكافل	\N
13	8	عرض بيانات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:26.912917+02	مسؤول كلية	تكافل	\N
14	8	موافقة مبدئية	\N	33	\N	::1	2025-12-04 23:45:28.617956+02	مسؤول كلية	تكافل	\N
15	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:28.783895+02	مسؤول كلية	تكافل	\N
16	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:29.340688+02	مسؤول كلية	تكافل	\N
17	8	عرض بيانات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:29.34515+02	مسؤول كلية	تكافل	\N
18	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:44.435615+02	مسؤول كلية	تكافل	\N
19	8	موافقة طلب	\N	33	\N	::1	2025-12-04 23:45:46.419337+02	مسؤول كلية	تكافل	\N
20	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:46.474842+02	مسؤول كلية	تكافل	\N
21	8	عرض بيانات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:46.850048+02	مسؤول كلية	تكافل	\N
22	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:45:46.940228+02	مسؤول كلية	تكافل	\N
23	11	عرض بيانات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:47:03.074647+02	مشرف النظام	تكافل	\N
24	11	عرض بيانات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:47:03.133296+02	مشرف النظام	تكافل	\N
25	11	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:47:03.174881+02	مشرف النظام	تكافل	\N
26	11	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:47:03.337316+02	مشرف النظام	تكافل	\N
27	11	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:47:15.514875+02	مشرف النظام	تكافل	\N
28	11	عرض بيانات الطلب	\N	33	\N	127.0.0.1	2025-12-04 23:47:15.519219+02	مشرف النظام	تكافل	\N
29	11	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-12-04 23:48:14.601658+02	مشرف النظام	تكافل	\N
30	11	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-12-04 23:48:14.61752+02	مشرف النظام	تكافل	\N
31	11	عرض بيانات الطلب	\N	34	\N	127.0.0.1	2025-12-04 23:48:14.663616+02	مشرف النظام	تكافل	\N
32	11	عرض مستندات الطلب	\N	34	\N	127.0.0.1	2025-12-04 23:48:14.768899+02	مشرف النظام	تكافل	\N
33	8	عرض مستندات الطلب	\N	33	\N	127.0.0.1	2025-12-05 01:23:51.357149+02	مسؤول كلية	تكافل	\N
35	1	انشاء اسر	\N	\N	4	::1	2025-12-06 23:12:48.322893+02	\N	اسر	\N
36	1	انشاء اسر	\N	\N	5	::1	2025-12-06 23:22:21.065833+02	\N	اسر	\N
37	1	انشاء اسر	\N	\N	6	::1	2025-12-06 23:30:14.220609+02	\N	اسر	\N
38	5	انشاء نشاط	9	\N	\N	::1	2025-12-07 16:56:05.822507+02	\N	نشاط	\N
39	1	انشاء نشاط	10	\N	\N	::1	2025-12-07 17:16:53.936357+02	\N	نشاط	\N
40	1	انشاء نشاط	11	\N	\N	::1	2025-12-07 17:18:45.664426+02	\N	نشاط	\N
41	1	انشاء نشاط	12	\N	\N	::1	2025-12-07 17:19:10.520774+02	\N	نشاط	\N
42	1	انشاء نشاط	13	\N	\N	::1	2025-12-07 17:19:12.852932+02	\N	نشاط	\N
43	1	انشاء نشاط	14	\N	\N	::1	2025-12-07 17:19:44.659706+02	\N	نشاط	\N
44	1	انشاء نشاط	15	\N	\N	::1	2025-12-07 17:20:41.032842+02	\N	نشاط	\N
45	1	انشاء نشاط	16	\N	\N	::1	2025-12-07 17:21:03.009174+02	\N	نشاط	\N
46	1	انشاء نشاط	17	\N	\N	::1	2025-12-07 17:44:36.565946+02	\N	نشاط	\N
47	1	انشاء نشاط	18	\N	\N	::1	2025-12-07 17:45:35.736247+02	\N	نشاط	\N
48	1	انشاء نشاط	19	\N	\N	::1	2025-12-07 17:47:51.603572+02	\N	نشاط	\N
49	1	انشاء نشاط	20	\N	\N	::1	2025-12-07 17:48:38.107738+02	\N	نشاط	\N
50	1	انشاء نشاط	21	\N	\N	::1	2025-12-07 17:59:21.061125+02	\N	نشاط	\N
51	1	انشاء نشاط	22	\N	\N	::1	2025-12-07 18:00:28.202926+02	\N	نشاط	\N
52	1	انشاء نشاط	23	\N	\N	::1	2025-12-07 18:01:34.368527+02	\N	نشاط	\N
53	1	انشاء نشاط	24	\N	\N	::1	2025-12-07 18:05:37.288029+02	\N	نشاط	\N
54	1	انشاء نشاط	25	\N	\N	::1	2025-12-07 18:07:47.105435+02	\N	نشاط	\N
55	1	انشاء نشاط	26	\N	\N	::1	2025-12-07 18:10:20.311507+02	\N	نشاط	\N
56	1	انشاء نشاط	27	\N	\N	::1	2025-12-07 18:12:30.50403+02	\N	نشاط	\N
57	1	انشاء نشاط	28	\N	\N	::1	2025-12-07 18:19:58.057556+02	\N	نشاط	\N
58	1	انشاء نشاط	29	\N	\N	::1	2025-12-07 18:21:19.632927+02	\N	نشاط	\N
59	1	انشاء نشاط	30	\N	\N	::1	2025-12-07 18:25:56.956283+02	\N	نشاط	\N
60	5	عرض بيانات الطلب	\N	25	\N	127.0.0.1	2025-12-08 12:04:41.368333+02	مدير ادارة	تكافل	\N
61	5	عرض بيانات الطلب	\N	25	\N	127.0.0.1	2025-12-08 12:04:41.527036+02	مدير ادارة	تكافل	\N
62	5	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-12-08 12:04:41.63543+02	مدير ادارة	تكافل	\N
63	5	عرض مستندات الطلب	\N	25	\N	127.0.0.1	2025-12-08 12:04:41.841641+02	مدير ادارة	تكافل	\N
71	1	انشاء اسر	\N	\N	14	::1	2025-12-11 23:13:26.604682+02	\N	اسر	\N
73	1	انشاء اسر	\N	\N	16	::1	2025-12-11 23:16:04.292656+02	\N	اسر	\N
76	1	انشاء اسر	\N	\N	19	::1	2025-12-11 23:30:45.910745+02	\N	اسر	\N
77	1	انشاء نشاط	31	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
78	1	انشاء نشاط	32	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
79	1	انشاء نشاط	33	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
80	1	انشاء نشاط	34	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
81	1	انشاء نشاط	35	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
82	1	انشاء نشاط	36	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
83	1	انشاء نشاط	37	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
84	1	انشاء نشاط	38	\N	\N	::1	2025-12-11 23:30:45.910745+02	\N	نشاط	\N
85	1	انشاء اسر	\N	\N	20	::1	2025-12-11 23:34:26.155201+02	\N	اسر	\N
86	1	انشاء نشاط	39	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
87	1	انشاء نشاط	40	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
88	1	انشاء نشاط	41	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
89	1	انشاء نشاط	42	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
90	1	انشاء نشاط	43	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
91	1	انشاء نشاط	44	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
92	1	انشاء نشاط	45	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
93	1	انشاء نشاط	46	\N	\N	::1	2025-12-11 23:34:26.155201+02	\N	نشاط	\N
94	1	انشاء اسر	\N	\N	21	::1	2025-12-12 00:55:32.001674+02	\N	اسر	\N
95	1	انشاء نشاط	47	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
96	1	انشاء نشاط	48	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
97	1	انشاء نشاط	49	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
98	1	انشاء نشاط	50	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
99	1	انشاء نشاط	51	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
100	1	انشاء نشاط	52	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
101	1	انشاء نشاط	53	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
102	1	انشاء نشاط	54	\N	\N	::1	2025-12-12 00:55:32.001674+02	\N	نشاط	\N
103	1	انشاء نشاط	55	\N	\N	::1	2025-12-12 02:11:20.195062+02	\N	نشاط	\N
104	8	عرض بيانات الطلب	\N	21	\N	127.0.0.1	2025-12-12 02:59:09.375005+02	مسؤول كلية	تكافل	\N
105	8	عرض تفاصيل الأسرة	\N	\N	20	127.0.0.1	2025-12-12 03:04:35.621213+02	مسؤول كلية	اسر	\N
106	8	عرض تفاصيل الأسرة	\N	\N	20	127.0.0.1	2025-12-12 03:07:07.802433+02	مسؤول كلية	اسر	\N
107	8	موافقة طلب	\N	13	\N	::1	2025-12-12 03:19:11.77522+02	مسؤول كلية	تكافل	\N
108	8	موافقة مبدئية وتحديد الشروط	\N	\N	1	127.0.0.1	2025-12-14 17:43:17.613796+02	مسؤول كلية	اسر	\N
109	8	رفض طلب إنشاء أسرة	\N	\N	4	127.0.0.1	2025-12-14 17:44:27.360495+02	مسؤول كلية	اسر	\N
110	8	حذف عضو من أسرة	\N	\N	1	127.0.0.1	2025-12-14 17:51:51.287681+02	مسؤول كلية	اسر	\N
111	8	حذف عضو من أسرة	\N	\N	2	127.0.0.1	2025-12-14 17:52:20.190925+02	مسؤول كلية	اسر	\N
112	10	موافقة نهائية (إدارة مركزية)	\N	\N	2	127.0.0.1	2025-12-14 18:07:08.394181+02	مشرف النظام	اسر	\N
113	10	رفض الأسرة (إدارة مركزية)	\N	\N	1	127.0.0.1	2025-12-14 18:07:19.105108+02	مشرف النظام	اسر	\N
115	8	حذف عضو من أسرة	\N	\N	1	127.0.0.1	2026-01-17 02:53:10.48671+02	مسؤول كلية	اسر	\N
116	8	منح صلاحية إنشاء أسرة للطالب	\N	\N	\N	127.0.0.1	2026-01-19 01:31:44.49988+02	مسؤول كلية	طالب	15
117	8	منح صلاحية إنشاء أسرة للطالب	\N	\N	\N	127.0.0.1	2026-01-19 01:32:48.863882+02	مسؤول كلية	طالب	11
118	8	سحب صلاحية إنشاء أسرة من الطالب	\N	\N	\N	127.0.0.1	2026-01-19 01:35:42.024131+02	مسؤول كلية	طالب	11
119	16	رفض الأسرة (إدارة مركزية)	\N	\N	3	127.0.0.1	2026-01-20 16:16:04.820561+02	مدير ادارة	اسر	\N
\.


--
-- Data for Name: plans; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.plans (plan_id, name, term, created_at, updated_at, faculty_id) FROM stdin;
\.


--
-- Data for Name: posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.posts (post_id, title, description, family_id, faculty_id, created_at, updated_at) FROM stdin;
1	test	first test for posts at family 1	1	1	2025-12-06 23:37:53.830965	2025-12-06 23:37:53.830977
2	hellooo	this is a hello	20	1	2025-12-12 00:09:07.412746	2025-12-12 00:09:07.412758
3	hello	test post	6	1	2026-01-19 00:32:56.010437	2026-01-19 00:32:56.010449
\.


--
-- Data for Name: prtcps; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.prtcps (event_id, student_id, rank, reward, status, id) FROM stdin;
3	13	\N	\N	منتظر	3
6	2	\N	\N	مقبول	2
6	13	\N	\N	مقبول	4
6	11	\N	\N	مرفوض	1
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
28	22	1	مقبول	2025-11-22 21:25:05.521407+02	5	working	working	200.00	200.00	400.00	2	+201254578545	+201254578555	rture	نعم	امتياز	انتظام	eg	8	2025-11-22 21:26:29.8242+02	\N	ملك	1700	f	{"خصم كتاب","خصم انتظام"}
16	13	1	منتظر	2025-11-09 23:46:04.397043+02	1	string	string	500.00	400.00	900.00	1	+20155255	+20355555	string	t	string	string	eg	8	2025-11-21 21:09:24.807247+02	\N	ملك	600	f	{"خصم انتظام","خصم كتاب"}
33	13	1	مقبول	2025-11-22 22:38:56.450304+02	20	متوفي	حي	0.00	200.00	200.00	2	+2012124588	+20121212122	string	t	string	string	string	8	2025-12-04 23:45:46.419337+02	\N	ملك	500	f	{"خصم كتاب","خصم انتساب"}
13	13	1	مقبول	2025-11-09 23:26:39.736181+02	1	string	string	500.00	400.00	900.00	1	+20155255	+20355555	string	t	string	string	eg	8	2025-12-12 03:19:11.77522+02	\N	ملك	500	f	{"خصم كامل"}
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

COPY public.students (student_id, name, email, password, faculty_id, profile_photo, gender, nid, uid, phone_number, address, acd_year, join_date, gpa, grade, major, google_id, google_picture, is_google_auth, auth_method, last_login_method, last_google_login, can_create_fam) FROM stdin;
2	ليلى خالد	l.khaled@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	2	\N	F	223456789	887654321	+966555555555	جدة	2025/2026	2025-09-01	\N	\N	كيمياء	\N	\N	f	email	\N	\N	f
13	S	S@gmail.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	F	50248798445487	57857	20125455785	Eg	2025	2025-09-01	\N	\N	hg	\N	\N	f	email	\N	\N	f
16	std3	std3@gmail.com	$2b$12$Fugft7.jfR0j.SYKQzEoj.YYEJUrQ5EpG1gJMEidLcHMGWkSZQua6	2	uploads/students/16/image.jpg	M	5055258	202255	+2012555	cairo	2	2025-11-14	\N	good	hw	\N	\N	f	email	\N	\N	f
17	std4	std4@gmail.com	$2b$12$ZXUb7ed4gWa.he7wbwiuFOCWgv5HITlD6spFMSpfi5Z3wRqt6Tzde	2	uploads/students/17/image.jpg	M	5555555	555555	202222222	eg	انتظام	2025-11-15	\N	جيد	sw	\N	\N	f	email	\N	\N	f
14	std1	s1@gmail.com	$2b$12$YRVhES6M.epwXXJfInQbNuOwDgIW9rHV8ODgyVUR8c3IqN2hpxKHC	2	uploads/students/14/image.jpg	M	20125888888	202251	2022222555	giza	4	2025-11-14	\N	جيد	H.w	\N	\N	f	email	\N	\N	f
18	std5	atd5@gmail.com	pbkdf2_sha256$1000000$sfWYqdwxjgzHDBMi0vd4Ky$Ymb1IAclnoHPYPPy8BYYbEpCguZHGHnr3VR6cLRcCPE=	2	uploads/students/18/image.jpg	M	20121545454	201215	203212154	eg	1	2025-11-18	\N	good	sw	\N	\N	f	email	\N	\N	f
19	std6	std5@gmail.com	$2b$12$WXE1vocFatp5QGZCnZdrpun3D7Kckrf8SF2RK4nYiO6xpFbEdhXn.	2	uploads/students/19/image.jpg	M	201215454540	2012150	2032121540	eg	1	2025-11-18	\N	good	sw	\N	\N	f	email	\N	\N	f
20	std10	std10@gmail.com	$2b$12$PD4cIEMPzqUx.o12xpBK7uNBUCqLlEDjitF63WblHy6tLeLrphOd2	2	uploads/students/20/image.jpg	M	2012154545404	20121504	20321215404	eg	1	2025-11-18	\N	good	sw	\N	\N	f	email	\N	\N	f
21	std11	std11@gmail.com	$2b$12$6gmbgzKH/sg/zFC2MbDLne.V3.bqQJatU1DVfflq46LkGUUd2WD3O	2	uploads/students/21/image.jpg	M	201215454540401	201215040011	2032121540400	eg	1	2025-11-18	\N	good	sw	\N	\N	f	email	\N	\N	f
22	omaromar	omaromar@gmail.com	$2b$12$NE14tF5M6Ac5JUVqx57t.eoS647kz1BtneSY0jKVEYkGwiTnVPEz6	1	uploads/students/22/image.jpg	m	20122222222	1122222	2012222222	eg	1	2025-11-22	\N	good	sw	\N	\N	f	email	\N	\N	f
34	lili	lili@gmail.com	$2b$12$BZUrkC7Ifb.lO73hp82ceeqM2JmRzjSF719L5r/.MVVXvihJlcpQu	1	\N	m	30212545874785	254874	20121215452	egypt	one	2025-12-03	\N	\N	sw	\N	\N	f	email	\N	\N	f
35	aliali	alialiali@gmail.com	$2b$12$x.gPie/ARxDZ6IqFm.vvyeJpTsMJIkfMGTi8.6.y.v1RVKr2RXC5m	2	\N	M	20121254587458	222222	2012235522	egypt	3	2025-12-03	\N	\N	sw	\N	\N	f	email	\N	\N	f
29	tempoo	teempoomail00@gmail.com	$2b$12$9flfKPu.mT3xkFT82.1DYeaCLnyWtp5BC98YGCSSTSOPy2/r2N85e	1	\N	M	21212145487896	636598	2322020202	egypt	one	2025-12-02	\N	\N	sw	109603782548753839934	https://lh3.googleusercontent.com/a/ACg8ocKuNIi_4kHTkrXpZo_B0l85u7PjeSKevmApCg59GTZi0uPpPg=s96-c	t	google	google	2025-12-12 15:26:37.185208	f
1	محمد سعيد	m.saeed@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	M	123456789	987654321	+966501234567	الرياض	2025/2026	2025-09-01	\N	جيد جدا	هندسة حاسوب	\N	\N	f	email	\N	\N	t
28	aloalo	alolo@gmail.com	$2b$12$MMVtnfjNS8aWKC4V.plX1ObsIyAtsphd1tKE7pramj5ZoHE7e.sUy	1	\N	m	20121545478454	252525	+20121221212	egypt	1	2025-12-02	\N	\N	sw	\N	\N	f	email	\N	\N	t
15	std2	std2@gmail.com	$2b$12$SngL6dkYpJ4WEPMQ2URgqOS4i4yBR1QGgHgWzJzqsmX9NawEBZhru	1	uploads/students/15/image.jpg	M	2021254587	2021245	+201254578	eg	4	2025-11-14	\N	ممتاز	sw	\N	\N	f	email	\N	\N	t
11	A	AA@gmail.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	F	50248798655487	55857	20125455485	Eg	2025	2025-09-01	\N	\N	hg	\N	\N	f	email	\N	\N	f
36	علي	ali5@gmail.com	$2b$12$lVLBcoy0XpkOnR2BEHF.hOZ2i69cCOXas.dtibIA5ed30n1kZgLf6	3	\N	M	201212548789666	20121210	20124545255	egypt	1	2025-12-04	\N	\N	sw	\N	\N	f	email	\N	\N	f
39	test2	test2@gmail.com	$2b$12$uAzWg3XMnY4cH3UsJwscSuzSjIoGdlhyKB9Q2M1rzZU2aiEIvoM4u	1	\N	m	20255555555557	34235	2012222277	string	string	2026-01-17	\N	string	string	\N	\N	f	email	\N	\N	f
37	ssh	ssh493147@gmail.com	$2b$12$wyBkhAzvgNLV7SXZ15kKEuFX3Fv8JkfyxDDC8XoLYP/vv.TACot.O	3	\N	M	201215458747845	20121545	20124504850	egypt	one	2025-12-09	\N	\N	sdfs	108654151463126841079	https://lh3.googleusercontent.com/a/ACg8ocJOdPnMOecixsR8HSe3rh1b64btth_Gn1n3zcDYWxRxa71-BQ=s96-c	t	google	google	2026-01-19 15:18:50.189769	f
38	test	test@gmail.com	$2b$12$BmXBa75oYnvp938Ak2mTwe//1uqRabCui3RNL7mz7af75f70Qdioe	1	\N	m	gAAAAABpa46bTpr2_6EudLrpOGB-3l0EHSPsC7k5_M9i2tPDnMqTfwYhyhQpz4bpLEoGaTXTGu68Vui9sQX5Ivgfb9ILtN40Sg==	gAAAAABpa46bKy9cA6u63ZCKnzWim5dwcbAjeWFltHGqW6P2xnvX0cN2qknajz3QY72DHaAt-6Wqlut6zK6I3LMWb7CngZOecA==	gAAAAABpa46bHBXFLnrKkRsAfB3rtoFXD_9RwT1hqdu1PH5Oblo9JCpB-lU0m9SB9Awi-AmD-5yil78W85gTP5Tn0cpWXwdAjg==	gAAAAABpa46b4ShYUDqT9bO914NaCmsQ7LevnDse6JGULVKiryPs-MgUAkJKi_YnN0pJZzAeo4sO8EZIBT98sq7YaFNA6uV18Q==	string	2026-01-17	\N	string	string	\N	\N	f	email	\N	\N	f
\.


--
-- Name: admins_admin_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admins_admin_id_seq', 21, true);


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

SELECT pg_catalog.setval('public.departments_dept_id_seq', 7, true);


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

SELECT pg_catalog.setval('public.events_event_id_seq', 55, true);


--
-- Name: faculties_faculty_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.faculties_faculty_id_seq', 3, true);


--
-- Name: families_family_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.families_family_id_seq', 21, true);


--
-- Name: family_admins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.family_admins_id_seq', 60, true);


--
-- Name: logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.logs_log_id_seq', 119, true);


--
-- Name: plans_plan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.plans_plan_id_seq', 1, false);


--
-- Name: posts_post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.posts_post_id_seq', 3, true);


--
-- Name: prtcps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.prtcps_id_seq', 4, true);


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

SELECT pg_catalog.setval('public.students_student_id_seq', 39, true);


--
-- Name: admins admins_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_email_key UNIQUE (email);


--
-- Name: admins admins_national_id_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_national_id_unique UNIQUE (nid);


--
-- Name: admins admins_phone_number_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_phone_number_unique UNIQUE (phone_number);


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
-- Name: family_admins family_admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.family_admins
    ADD CONSTRAINT family_admins_pkey PRIMARY KEY (id);


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
-- Name: plans plans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_pkey PRIMARY KEY (plan_id);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (post_id);


--
-- Name: prtcps prtcps_event_student_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_event_student_unique UNIQUE (event_id, student_id);


--
-- Name: prtcps prtcps_id_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_id_pkey PRIMARY KEY (id);


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
-- Name: students students_google_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_google_id_key UNIQUE (google_id);


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
-- Name: idx_events_plan_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_plan_id ON public.events USING btree (plan_id) WITH (deduplicate_items='true');


--
-- Name: idx_events_selected_facs; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_selected_facs ON public.events USING gin (selected_facs);


--
-- Name: idx_families_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_families_created_by ON public.families USING btree (created_by);


--
-- Name: idx_families_faculty_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_families_faculty_id ON public.families USING btree (faculty_id);


--
-- Name: idx_family_admins_family_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_family_admins_family_id ON public.family_admins USING btree (family_id);


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
-- Name: idx_logs_student_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_logs_student_id ON public.logs USING btree (student_id) WITH (fillfactor='100', deduplicate_items='true');


--
-- Name: idx_logs_target; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_logs_target ON public.logs USING btree (target_type, event_id, solidarity_id, family_id);


--
-- Name: idx_plans_faculty_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plans_faculty_id ON public.plans USING btree (faculty_id);


--
-- Name: idx_plans_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plans_name ON public.plans USING btree (name) WITH (fillfactor='100', deduplicate_items='true');


--
-- Name: idx_posts_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_posts_created_at ON public.posts USING btree (created_at DESC);


--
-- Name: idx_posts_faculty_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_posts_faculty_id ON public.posts USING btree (faculty_id);


--
-- Name: idx_posts_family_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_posts_family_id ON public.posts USING btree (family_id);


--
-- Name: idx_prtcps_event; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_prtcps_event ON public.prtcps USING btree (event_id);


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
-- Name: events events_plan_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_plan_fk FOREIGN KEY (plan_id) REFERENCES public.plans(plan_id) ON DELETE SET NULL;


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
-- Name: family_admins fk_admin_family; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.family_admins
    ADD CONSTRAINT fk_admin_family FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE CASCADE;


--
-- Name: events fk_events_family; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_events_family FOREIGN KEY (family_id) REFERENCES public.families(family_id);


--
-- Name: family_members fk_family_members_dept; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT fk_family_members_dept FOREIGN KEY (dept_id) REFERENCES public.departments(dept_id);


--
-- Name: posts fk_posts_faculty; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_posts_faculty FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE CASCADE;


--
-- Name: posts fk_posts_family; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_posts_family FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE CASCADE;


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
-- Name: logs logs_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE SET NULL;


--
-- Name: plans plans_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


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

\unrestrict Hcop7CUbwNSQjhcDJt2N3PDcYTP9rXEz8VivpXQBnWgXCVrAgNEcyig6xPtOdRM

