--
-- PostgreSQL database dump
--

\restrict FgEvPnb4vKUwFhebrlXhcLLcPEu5bhbQ9n1fkcbffSU0NIiS54C4DuqyRWdLH24

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

ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_faculty_fk;
ALTER TABLE IF EXISTS ONLY public.solidarity_docs DROP CONSTRAINT IF EXISTS solidarity_docs_solidarity_id_fkey;
ALTER TABLE IF EXISTS ONLY public.solidarities DROP CONSTRAINT IF EXISTS solidarities_student_fk;
ALTER TABLE IF EXISTS ONLY public.solidarities DROP CONSTRAINT IF EXISTS solidarities_faculty_fk;
ALTER TABLE IF EXISTS ONLY public.solidarities DROP CONSTRAINT IF EXISTS solidarities_approved_by_fk;
ALTER TABLE IF EXISTS ONLY public.prtcps DROP CONSTRAINT IF EXISTS prtcps_student_fk;
ALTER TABLE IF EXISTS ONLY public.prtcps DROP CONSTRAINT IF EXISTS prtcps_event_fk;
ALTER TABLE IF EXISTS ONLY public.plans DROP CONSTRAINT IF EXISTS plans_faculty_fk;
ALTER TABLE IF EXISTS ONLY public.plans DROP CONSTRAINT IF EXISTS plans_dept_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plans DROP CONSTRAINT IF EXISTS plans_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.logs DROP CONSTRAINT IF EXISTS logs_student_fk;
ALTER TABLE IF EXISTS ONLY public.logs DROP CONSTRAINT IF EXISTS logs_solidarity_fk;
ALTER TABLE IF EXISTS ONLY public.logs DROP CONSTRAINT IF EXISTS logs_family_fk;
ALTER TABLE IF EXISTS ONLY public.logs DROP CONSTRAINT IF EXISTS logs_event_fk;
ALTER TABLE IF EXISTS ONLY public.logs DROP CONSTRAINT IF EXISTS logs_actor_fk;
ALTER TABLE IF EXISTS ONLY public.posts DROP CONSTRAINT IF EXISTS fk_posts_family;
ALTER TABLE IF EXISTS ONLY public.posts DROP CONSTRAINT IF EXISTS fk_posts_faculty;
ALTER TABLE IF EXISTS ONLY public.scout_members DROP CONSTRAINT IF EXISTS fk_member_student;
ALTER TABLE IF EXISTS ONLY public.scout_members DROP CONSTRAINT IF EXISTS fk_member_group;
ALTER TABLE IF EXISTS ONLY public.scout_members DROP CONSTRAINT IF EXISTS fk_member_clan;
ALTER TABLE IF EXISTS ONLY public.scout_members DROP CONSTRAINT IF EXISTS fk_member_admin;
ALTER TABLE IF EXISTS ONLY public.clan_groups DROP CONSTRAINT IF EXISTS fk_group_clan;
ALTER TABLE IF EXISTS ONLY public.family_members DROP CONSTRAINT IF EXISTS fk_family_members_dept;
ALTER TABLE IF EXISTS ONLY public.events DROP CONSTRAINT IF EXISTS fk_events_family;
ALTER TABLE IF EXISTS ONLY public.clans DROP CONSTRAINT IF EXISTS fk_clan_faculty;
ALTER TABLE IF EXISTS ONLY public.clans DROP CONSTRAINT IF EXISTS fk_clan_admin;
ALTER TABLE IF EXISTS ONLY public.family_admins DROP CONSTRAINT IF EXISTS fk_admin_family;
ALTER TABLE IF EXISTS ONLY public.family_members DROP CONSTRAINT IF EXISTS family_members_student_fk;
ALTER TABLE IF EXISTS ONLY public.family_members DROP CONSTRAINT IF EXISTS family_members_family_fk;
ALTER TABLE IF EXISTS ONLY public.families DROP CONSTRAINT IF EXISTS families_faculty_fk;
ALTER TABLE IF EXISTS ONLY public.families DROP CONSTRAINT IF EXISTS families_created_by_fk;
ALTER TABLE IF EXISTS ONLY public.families DROP CONSTRAINT IF EXISTS families_approved_by_fk;
ALTER TABLE IF EXISTS ONLY public.events DROP CONSTRAINT IF EXISTS events_plan_fk;
ALTER TABLE IF EXISTS ONLY public.events DROP CONSTRAINT IF EXISTS events_faculty_fk;
ALTER TABLE IF EXISTS ONLY public.events DROP CONSTRAINT IF EXISTS events_dept_fk;
ALTER TABLE IF EXISTS ONLY public.events DROP CONSTRAINT IF EXISTS events_created_by_fk;
ALTER TABLE IF EXISTS ONLY public.event_docs DROP CONSTRAINT IF EXISTS event_docs_uploaded_by_fkey;
ALTER TABLE IF EXISTS ONLY public.event_docs DROP CONSTRAINT IF EXISTS event_docs_event_id_fkey;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_auth_user_id;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_content_type_id_c4bce8eb_fk_django_co;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_user_id_6a12ed8b_fk_auth_user_id;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_group_id_97559544_fk_auth_group_id;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_content_type_id_2f476e4b_fk_django_co;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_group_id_b120cbf9_fk_auth_group_id;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissio_permission_id_84c5c92e_fk_auth_perm;
ALTER TABLE IF EXISTS ONLY public.admins DROP CONSTRAINT IF EXISTS admins_faculty_fk;
ALTER TABLE IF EXISTS ONLY public.admins DROP CONSTRAINT IF EXISTS admins_dept_fk;
DROP TRIGGER IF EXISTS trg_solidarities_touch ON public.solidarities;
DROP TRIGGER IF EXISTS trg_families_touch ON public.families;
DROP TRIGGER IF EXISTS trg_events_touch ON public.events;
DROP INDEX IF EXISTS public.idx_students_faculty_id;
DROP INDEX IF EXISTS public.idx_solidarities_student;
DROP INDEX IF EXISTS public.idx_solidarities_faculty;
DROP INDEX IF EXISTS public.idx_refresh_tokens_user;
DROP INDEX IF EXISTS public.idx_refresh_tokens_hash;
DROP INDEX IF EXISTS public.idx_refresh_tokens_expires;
DROP INDEX IF EXISTS public.idx_prtcps_student;
DROP INDEX IF EXISTS public.idx_prtcps_event;
DROP INDEX IF EXISTS public.idx_posts_family_id;
DROP INDEX IF EXISTS public.idx_posts_faculty_id;
DROP INDEX IF EXISTS public.idx_posts_created_at;
DROP INDEX IF EXISTS public.idx_plans_name;
DROP INDEX IF EXISTS public.idx_plans_faculty_id;
DROP INDEX IF EXISTS public.idx_plans_dept_id;
DROP INDEX IF EXISTS public.idx_plans_created_by;
DROP INDEX IF EXISTS public.idx_logs_target;
DROP INDEX IF EXISTS public.idx_logs_student_id;
DROP INDEX IF EXISTS public.idx_logs_logged_at;
DROP INDEX IF EXISTS public.idx_logs_actor_id;
DROP INDEX IF EXISTS public.idx_logs_action;
DROP INDEX IF EXISTS public.idx_family_members_student;
DROP INDEX IF EXISTS public.idx_family_admins_family_id;
DROP INDEX IF EXISTS public.idx_families_faculty_id;
DROP INDEX IF EXISTS public.idx_families_created_by;
DROP INDEX IF EXISTS public.idx_events_selected_facs;
DROP INDEX IF EXISTS public.idx_events_plan_id;
DROP INDEX IF EXISTS public.idx_events_faculty_id;
DROP INDEX IF EXISTS public.idx_events_dept_id;
DROP INDEX IF EXISTS public.idx_events_created_by;
DROP INDEX IF EXISTS public.idx_event_docs_uploaded_by;
DROP INDEX IF EXISTS public.idx_event_docs_uploaded_at;
DROP INDEX IF EXISTS public.idx_event_docs_event_id;
DROP INDEX IF EXISTS public.idx_event_docs_event;
DROP INDEX IF EXISTS public.idx_admins_faculty_id;
DROP INDEX IF EXISTS public.idx_admins_dept_id;
DROP INDEX IF EXISTS public.django_session_session_key_c0390e0f_like;
DROP INDEX IF EXISTS public.django_session_expire_date_a5c62663;
DROP INDEX IF EXISTS public.django_admin_log_user_id_c564eba6;
DROP INDEX IF EXISTS public.django_admin_log_content_type_id_c4bce8eb;
DROP INDEX IF EXISTS public.auth_user_username_6821ab7c_like;
DROP INDEX IF EXISTS public.auth_user_user_permissions_user_id_a95ead1b;
DROP INDEX IF EXISTS public.auth_user_user_permissions_permission_id_1fbb5f2c;
DROP INDEX IF EXISTS public.auth_user_groups_user_id_6a12ed8b;
DROP INDEX IF EXISTS public.auth_user_groups_group_id_97559544;
DROP INDEX IF EXISTS public.auth_permission_content_type_id_2f476e4b;
DROP INDEX IF EXISTS public.auth_group_permissions_permission_id_84c5c92e;
DROP INDEX IF EXISTS public.auth_group_permissions_group_id_b120cbf9;
DROP INDEX IF EXISTS public.auth_group_name_a6ea08ec_like;
ALTER TABLE IF EXISTS ONLY public.scout_members DROP CONSTRAINT IF EXISTS unique_student_clan;
ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_uid_key;
ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_pkey;
ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_phone_number_key;
ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_nid_key;
ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_google_id_key;
ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_email_key;
ALTER TABLE IF EXISTS ONLY public.solidarity_docs DROP CONSTRAINT IF EXISTS solidarity_docs_solidarity_id_doc_type_key;
ALTER TABLE IF EXISTS ONLY public.solidarity_docs DROP CONSTRAINT IF EXISTS solidarity_docs_pkey;
ALTER TABLE IF EXISTS ONLY public.solidarities DROP CONSTRAINT IF EXISTS solidarities_pkey;
ALTER TABLE IF EXISTS ONLY public.scout_members DROP CONSTRAINT IF EXISTS scout_members_pkey;
ALTER TABLE IF EXISTS ONLY public.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_pkey;
ALTER TABLE IF EXISTS ONLY public.prtcps DROP CONSTRAINT IF EXISTS prtcps_id_pkey;
ALTER TABLE IF EXISTS ONLY public.prtcps DROP CONSTRAINT IF EXISTS prtcps_event_student_unique;
ALTER TABLE IF EXISTS ONLY public.posts DROP CONSTRAINT IF EXISTS posts_pkey;
ALTER TABLE IF EXISTS ONLY public.plans DROP CONSTRAINT IF EXISTS plans_pkey;
ALTER TABLE IF EXISTS ONLY public.logs DROP CONSTRAINT IF EXISTS logs_pkey;
ALTER TABLE IF EXISTS ONLY public.family_members DROP CONSTRAINT IF EXISTS family_members_pkey;
ALTER TABLE IF EXISTS ONLY public.family_admins DROP CONSTRAINT IF EXISTS family_admins_pkey;
ALTER TABLE IF EXISTS ONLY public.families DROP CONSTRAINT IF EXISTS families_pkey;
ALTER TABLE IF EXISTS ONLY public.faculties DROP CONSTRAINT IF EXISTS faculties_pkey;
ALTER TABLE IF EXISTS ONLY public.events DROP CONSTRAINT IF EXISTS events_pkey;
ALTER TABLE IF EXISTS ONLY public.event_docs DROP CONSTRAINT IF EXISTS event_docs_pkey;
ALTER TABLE IF EXISTS ONLY public.documents DROP CONSTRAINT IF EXISTS documents_pkey;
ALTER TABLE IF EXISTS ONLY public.django_session DROP CONSTRAINT IF EXISTS django_session_pkey;
ALTER TABLE IF EXISTS ONLY public.django_migrations DROP CONSTRAINT IF EXISTS django_migrations_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_app_label_model_76bd3d3b_uniq;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_pkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_pkey;
ALTER TABLE IF EXISTS ONLY public.clans DROP CONSTRAINT IF EXISTS clans_pkey;
ALTER TABLE IF EXISTS ONLY public.clans DROP CONSTRAINT IF EXISTS clans_faculty_id_key;
ALTER TABLE IF EXISTS ONLY public.clan_groups DROP CONSTRAINT IF EXISTS clan_groups_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_user DROP CONSTRAINT IF EXISTS auth_user_username_key;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permissions_user_id_permission_id_14a6b632_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_user DROP CONSTRAINT IF EXISTS auth_user_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_user_id_group_id_94350c0c_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_content_type_id_codename_01ab375a_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_group DROP CONSTRAINT IF EXISTS auth_group_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_group_id_permission_id_0cd325b0_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_group DROP CONSTRAINT IF EXISTS auth_group_name_key;
ALTER TABLE IF EXISTS ONLY public.admins DROP CONSTRAINT IF EXISTS admins_pkey;
ALTER TABLE IF EXISTS ONLY public.admins DROP CONSTRAINT IF EXISTS admins_phone_number_unique;
ALTER TABLE IF EXISTS ONLY public.admins DROP CONSTRAINT IF EXISTS admins_national_id_unique;
ALTER TABLE IF EXISTS ONLY public.admins DROP CONSTRAINT IF EXISTS admins_email_key;
ALTER TABLE IF EXISTS public.solidarity_docs ALTER COLUMN doc_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.scout_members ALTER COLUMN scout_member_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.refresh_tokens ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.prtcps ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.posts ALTER COLUMN post_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.family_admins ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.event_docs ALTER COLUMN doc_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.clans ALTER COLUMN clan_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.clan_groups ALTER COLUMN group_id DROP DEFAULT;
DROP TABLE IF EXISTS public.students;
DROP SEQUENCE IF EXISTS public.solidarity_docs_doc_id_seq;
DROP TABLE IF EXISTS public.solidarity_docs;
DROP TABLE IF EXISTS public.solidarities;
DROP SEQUENCE IF EXISTS public.scout_members_scout_member_id_seq;
DROP TABLE IF EXISTS public.scout_members;
DROP SEQUENCE IF EXISTS public.refresh_tokens_id_seq;
DROP TABLE IF EXISTS public.refresh_tokens;
DROP SEQUENCE IF EXISTS public.prtcps_id_seq;
DROP TABLE IF EXISTS public.prtcps;
DROP SEQUENCE IF EXISTS public.posts_post_id_seq;
DROP TABLE IF EXISTS public.posts;
DROP TABLE IF EXISTS public.plans;
DROP TABLE IF EXISTS public.logs;
DROP TABLE IF EXISTS public.family_members;
DROP SEQUENCE IF EXISTS public.family_admins_id_seq;
DROP TABLE IF EXISTS public.family_admins;
DROP TABLE IF EXISTS public.families;
DROP TABLE IF EXISTS public.faculties;
DROP TABLE IF EXISTS public.events;
DROP SEQUENCE IF EXISTS public.event_docs_doc_id_seq;
DROP TABLE IF EXISTS public.event_docs;
DROP TABLE IF EXISTS public.documents;
DROP TABLE IF EXISTS public.django_session;
DROP TABLE IF EXISTS public.django_migrations;
DROP TABLE IF EXISTS public.django_content_type;
DROP TABLE IF EXISTS public.django_admin_log;
DROP TABLE IF EXISTS public.departments;
DROP SEQUENCE IF EXISTS public.clans_clan_id_seq;
DROP TABLE IF EXISTS public.clans;
DROP SEQUENCE IF EXISTS public.clan_groups_group_id_seq;
DROP TABLE IF EXISTS public.clan_groups;
DROP TABLE IF EXISTS public.auth_user_user_permissions;
DROP TABLE IF EXISTS public.auth_user_groups;
DROP TABLE IF EXISTS public.auth_user;
DROP TABLE IF EXISTS public.auth_permission;
DROP TABLE IF EXISTS public.auth_group_permissions;
DROP TABLE IF EXISTS public.auth_group;
DROP TABLE IF EXISTS public.admins;
DROP FUNCTION IF EXISTS public.set_updated_at();
DROP FUNCTION IF EXISTS public.client_ip();
DROP TYPE IF EXISTS public.target_type;
DROP TYPE IF EXISTS public.sol_doc_type;
DROP TYPE IF EXISTS public.req_type_enum;
DROP TYPE IF EXISTS public.owner_type;
DROP TYPE IF EXISTS public.housing_status;
DROP TYPE IF EXISTS public.general_status;
DROP TYPE IF EXISTS public.family_type;
DROP TYPE IF EXISTS public.family_members_roles;
DROP TYPE IF EXISTS public.event_type;
DROP TYPE IF EXISTS public.admin_role;
DROP TYPE IF EXISTS public.actor_type;
--
-- Name: actor_type; Type: TYPE; Schema: public; Owner: -
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


--
-- Name: admin_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.admin_role AS ENUM (
    'مسؤول كلية',
    'مدير كلية',
    'مدير ادارة',
    'مدير عام',
    'مشرف النظام'
);


--
-- Name: event_type; Type: TYPE; Schema: public; Owner: -
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


--
-- Name: family_members_roles; Type: TYPE; Schema: public; Owner: -
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


--
-- Name: family_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.family_type AS ENUM (
    'نوعية',
    'مركزية',
    'اصدقاء البيئة'
);


--
-- Name: general_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.general_status AS ENUM (
    'موافقة مبدئية',
    'مقبول',
    'منتظر',
    'مرفوض',
    'قادم',
    'ملغي',
    'مكتمل'
);


--
-- Name: housing_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.housing_status AS ENUM (
    'ايجار',
    'ملك'
);


--
-- Name: owner_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.owner_type AS ENUM (
    'نشاط',
    'طالب',
    'تكافل',
    'اسر'
);


--
-- Name: req_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.req_type_enum AS ENUM (
    'مصاريف كتب',
    'مصاريف انتساب',
    'مصاريف انتظام',
    'مصاريف كاملة',
    'اخرى'
);


--
-- Name: sol_doc_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sol_doc_type AS ENUM (
    'بحث احتماعي',
    'اثبات دخل',
    'ص.ب ولي امر',
    'ص.ب شخصية',
    'حبازة زراعية',
    'تكافل و كرامة'
);


--
-- Name: target_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.target_type AS ENUM (
    'نشاط',
    'تكافل',
    'اسر',
    'اخر',
    'طالب',
    'جوالة'
);


--
-- Name: client_ip(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.client_ip() RETURNS inet
    LANGUAGE sql STABLE
    AS $$ SELECT COALESCE(inet_client_addr(), '0.0.0.0') $$;


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admins; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: admins_admin_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: auth_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: auth_user; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: clan_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clan_groups (
    group_id integer NOT NULL,
    name character varying(100) NOT NULL,
    clan_id integer NOT NULL,
    display_order integer DEFAULT 1,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: clan_groups_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clan_groups_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clan_groups_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clan_groups_group_id_seq OWNED BY public.clan_groups.group_id;


--
-- Name: clans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clans (
    clan_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    faculty_id integer,
    created_by integer,
    status character varying(20) DEFAULT 'نشط'::character varying,
    min_members integer DEFAULT 50,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: clans_clan_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clans_clan_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clans_clan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clans_clan_id_seq OWNED BY public.clans.clan_id;


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    dept_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    for_env_fam boolean DEFAULT false NOT NULL
);


--
-- Name: departments_dept_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: django_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: documents_doc_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: event_docs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: event_docs_doc_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.event_docs_doc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_docs_doc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_docs_doc_id_seq OWNED BY public.event_docs.doc_id;


--
-- Name: events; Type: TABLE; Schema: public; Owner: -
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
    st_date date NOT NULL,
    end_date date NOT NULL,
    s_limit integer,
    created_at timestamp with time zone DEFAULT now(),
    type public.event_type,
    family_id integer,
    resource character varying(100),
    selected_facs integer[],
    plan_id integer,
    active boolean DEFAULT false,
    rejection_reason text,
    CONSTRAINT events_check CHECK ((end_date >= st_date))
);


--
-- Name: events_event_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: faculties; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: faculties_faculty_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: families; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: families_family_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: family_admins; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: family_admins_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.family_admins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: family_admins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.family_admins_id_seq OWNED BY public.family_admins.id;


--
-- Name: family_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.family_members (
    family_id integer NOT NULL,
    student_id integer NOT NULL,
    role public.family_members_roles,
    status public.general_status DEFAULT 'منتظر'::public.general_status,
    joined_at timestamp with time zone DEFAULT now(),
    dept_id integer
);


--
-- Name: logs; Type: TABLE; Schema: public; Owner: -
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
    student_id integer
);


--
-- Name: logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plans (
    plan_id integer NOT NULL,
    name character varying(150) NOT NULL,
    term integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    faculty_id integer,
    dept_id integer,
    created_by integer
);


--
-- Name: plans_plan_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: posts; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: posts_post_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.posts_post_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: posts_post_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.posts_post_id_seq OWNED BY public.posts.post_id;


--
-- Name: prtcps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prtcps (
    event_id integer NOT NULL,
    student_id integer NOT NULL,
    rank integer,
    reward character varying(255),
    status public.general_status DEFAULT 'منتظر'::public.general_status,
    id bigint NOT NULL
);


--
-- Name: prtcps_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.prtcps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: prtcps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.prtcps_id_seq OWNED BY public.prtcps.id;


--
-- Name: refresh_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.refresh_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    user_type character varying(10) NOT NULL,
    token_hash character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone NOT NULL,
    is_revoked boolean DEFAULT false,
    ip_address character varying(45),
    device_info character varying(255),
    CONSTRAINT refresh_tokens_user_type_check CHECK (((user_type)::text = ANY ((ARRAY['student'::character varying, 'admin'::character varying])::text[])))
);


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.refresh_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.refresh_tokens_id_seq OWNED BY public.refresh_tokens.id;


--
-- Name: scout_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scout_members (
    scout_member_id integer NOT NULL,
    student_id integer NOT NULL,
    clan_id integer NOT NULL,
    group_id integer,
    role character varying(30) DEFAULT 'MEMBER'::character varying,
    status character varying(20) DEFAULT 'منتظر'::character varying,
    reviewed_by integer,
    rejection_reason text,
    reviewed_at timestamp without time zone,
    joined_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: scout_members_scout_member_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scout_members_scout_member_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scout_members_scout_member_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scout_members_scout_member_id_seq OWNED BY public.scout_members.scout_member_id;


--
-- Name: solidarities; Type: TABLE; Schema: public; Owner: -
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
    rejection_reason integer,
    CONSTRAINT solidarities_f_phone_num_check CHECK (((f_phone_num IS NULL) OR (f_phone_num ~ '^\+?[0-9]{6,15}$'::text))),
    CONSTRAINT solidarities_m_phone_num_check CHECK (((m_phone_num IS NULL) OR (m_phone_num ~ '^\+?[0-9]{6,15}$'::text))),
    CONSTRAINT solidarities_sd_check CHECK ((sd = ANY (ARRAY['t'::bpchar, 'f'::bpchar])))
);


--
-- Name: solidarities_solidarity_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: solidarity_docs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: solidarity_docs_doc_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.solidarity_docs_doc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: solidarity_docs_doc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solidarity_docs_doc_id_seq OWNED BY public.solidarity_docs.doc_id;


--
-- Name: students; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: students_student_id_seq; Type: SEQUENCE; Schema: public; Owner: -
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
-- Name: clan_groups group_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clan_groups ALTER COLUMN group_id SET DEFAULT nextval('public.clan_groups_group_id_seq'::regclass);


--
-- Name: clans clan_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clans ALTER COLUMN clan_id SET DEFAULT nextval('public.clans_clan_id_seq'::regclass);


--
-- Name: event_docs doc_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_docs ALTER COLUMN doc_id SET DEFAULT nextval('public.event_docs_doc_id_seq'::regclass);


--
-- Name: family_admins id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_admins ALTER COLUMN id SET DEFAULT nextval('public.family_admins_id_seq'::regclass);


--
-- Name: posts post_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts ALTER COLUMN post_id SET DEFAULT nextval('public.posts_post_id_seq'::regclass);


--
-- Name: prtcps id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prtcps ALTER COLUMN id SET DEFAULT nextval('public.prtcps_id_seq'::regclass);


--
-- Name: refresh_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('public.refresh_tokens_id_seq'::regclass);


--
-- Name: scout_members scout_member_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scout_members ALTER COLUMN scout_member_id SET DEFAULT nextval('public.scout_members_scout_member_id_seq'::regclass);


--
-- Name: solidarity_docs doc_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarity_docs ALTER COLUMN doc_id SET DEFAULT nextval('public.solidarity_docs_doc_id_seq'::regclass);


--
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.admins (admin_id, name, email, password, faculty_id, dept_id, created_at, can_create, can_update, can_read, can_delete, acc_status, role, dept_fac_ls, nid, phone_number) FROM stdin;
12	string	user@example.com	pbkdf2_sha256$1000000$IrRY86mbOwprrogP9aOI2H$2RgAvUXSAwxSeNHNhdSuu+RXGdAhwr9bghYxx5mvfZY=	1	\N	2025-11-15 03:13:03.29534+02	t	t	t	t	active	مسؤول كلية	{}	\N	\N
14	a4	ar@gmail.com.com	pbkdf2_sha256$1000000$zBktzHX9eDrOqSc9VSreRz$eFZqgCmqCYdzJ7TUfKZQoUaOXXPxgicfH1cyjNL31dQ=	\N	\N	2025-11-15 03:36:53.711315+02	t	t	t	t	active	مشرف النظام	{}	\N	\N
3	أحمد علي	ahmed.faculty@example.com	pbkdf2_sha256$1000000$k0IQx82TzGMhVAFEe6Y8Zl$oiR9QGJQIceP5VudDGMnLBdeXYfJPbgW1rmeNzobO0g=	3	\N	2025-10-20 02:53:23.217139+03	t	t	t	f	active	مسؤول كلية	{}	\N	\N
7	محمد سعيد	mohamed.super@example.com	pbkdf2_sha256$1000000$yOdSWDrX15vKLosN6Dp41Y$I5NAsjlV29vxASgyoBCPnikiCcl9wf9fPvCxXSHt4Ys=	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مشرف النظام	{}	\N	\N
21	ahmed	ahmedm@gmail.com	pbkdf2_sha256$1000000$St8cjm17fUYZx0iDOZwRy0$8HFztv938EE0udu8cAekPGKmbFDVRfrWClNO6R1xEfc=	\N	\N	2025-12-09 23:28:44.320432+02	t	t	t	t	active	مشرف النظام	{}	99739715871769	2012222222
17	aa	aa@gmail.com	pbkdf2_sha256$1000000$2dc1qpkT0K2Rvf8jYCZFGr$RYI8fid0TOn0KPMmVGLXDSb+4fCh2gtoN+F/KrCJ0RE=	2	\N	2025-11-18 21:42:50.130782+02	t	t	t	t	active	مسؤول كلية	{}	\N	\N
18	admin12	admin12@gmail.com	pbkdf2_sha256$1000000$sZ9BCWoeUQKBmW1h4mY3g8$QqXoHVTnnHG6Xtk3BeqX21BCFPeh1zN6RD1cWtz/Ads=	2	\N	2025-11-18 23:03:16.0987+02	t	t	t	t	نشط	مسؤول كلية	{}	\N	\N
1	ahmed	ahmed@gmail.com	pbkdf2_sha256$1000000$dx0GL2Uj1qVCDZa7x83045$0q9vmyfE+Bf0237qGzyUVvtqnJEauuW6eauxJra+CIM=	1	\N	2025-10-20 02:34:30.31113+03	t	t	t	t	active	مسؤول كلية	{}	\N	\N
19	admin33	admin33@example.com	pbkdf2_sha256$1000000$rEqE9UmuMQqskvYGjne6Nd$T0ST6Ew8rabU2sFpgL/o90T4uhB8PUvkNCzOOOYIUI4=	2	\N	2025-11-21 16:33:42.63292+02	t	t	t	t	active	مسؤول كلية	{}	\N	\N
16	oo	oo@gmail.com	pbkdf2_sha256$1000000$QXXplajwQLlKBLRkvWyEDG$j2Hy8tqFThcTmWs+C0g6pFfGvVtrklz/leeYU9X0WzI=	\N	4	2025-11-18 20:45:57.231286+02	t	t	t	t	active	مدير ادارة	{}	\N	\N
4	سارة محمد	sara.head@example.com	pbkdf2_sha256$1000000$tWpoF8OP4IE1aV50n3VaN1$5MXEKa42Qg5TkOKQ2z5Xt3ApE8rFcnik/P48TdyTWps=	1	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير كلية	{}	\N	\N
6	منى يوسف	mona.general@example.com	pbkdf2_sha256$1000000$zThP8QI7sBlQ2rpPcPBw0T$vq8n7gJqUzzdcC5NVkqRQUNtuVjnLH8AWCM3qWOXuIE=	\N	\N	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير عام	{}	\N	\N
23	ibrahim	ibrahim@gmail.com	pbkdf2_sha256$1000000$qlmFg3vsgcK7URzd8NHjzY$3bKY5rQf4ZC7miho+WCFSfyve2UKi3A+XZ3QR+QZPRQ=	3	\N	2026-03-13 00:32:50.015969+02	t	t	t	t	active	مدير كلية	{}	\N	\N
11	B	b@gmail.com	pbkdf2_sha256$1000000$wrgC5ZDwinGSr1g0SR8vrz$RZ3Xy50cG9qhkw+toLxLTBdGpMndW5G/SgY3Iewb9EE=	\N	\N	2025-10-30 02:09:47.364118+03	t	t	t	t	active	مشرف النظام	{}	\N	\N
25	omar	omar2@gmail.com	pbkdf2_sha256$1000000$jP9LD5YI7ZXH0tdOaXIbR7$zHDMZw87wWgYGNxkRjVAnpPwMIp+D5fjCXO5OAYOVZo=	1	\N	2026-04-16 02:56:32.400282+02	t	t	t	t	active	مسؤول كلية	{1,2,3,7}	\N	\N
9	ali	ali@gmail.com	pbkdf2_sha256$1000000$g5LSEHFQAOV5imJXliaDcS$EC34z7cDVSgQjTbt3313xwvXrj72TCS+GExZENNjMI4=	1	\N	2025-10-30 01:34:00.847159+03	t	t	t	t	active	مسؤول كلية	{}	\N	\N
2	سارة محمد	sara@example.com	pbkdf2_sha256$1000000$YOum6XQm4YPTyOygoretCH$qI6iJdP+RHVI5jCneq2CYhb88PnvNhsdvduSklDyMaI=	2	\N	2025-10-20 02:34:30.31113+03	t	t	t	f	active	مسؤول كلية	{}	\N	\N
15	ali	alioamar@gmail.com	pbkdf2_sha256$1000000$MYace5Oq8w4z1fOtwxrC3A$d8Vh8UhpL/6nKz4RcdwtRDIWAoso5ZxHTELq+wOJfMs=	1	\N	2025-11-18 20:27:49.844806+02	t	t	t	t	active	مسؤول كلية	{}	\N	\N
26	Mai	maioia@gmail.com	pbkdf2_sha256$1000000$eNnJyq9pTotcrEWCc7TI1d$MK0at7RBPUL4Rb/JesETxxq8jtXTjMGiaETt02+5s8Q=	3	\N	2026-04-16 06:05:52.966041+02	t	t	t	t	active	مشرف النظام	{}	\N	\N
22	احمد محمد علي	ahmed.mohamed.ali@gmail.com	pbkdf2_sha256$1000000$5RPz3vxDK2TMUFtVC9pPlF$fI5uqR/sJ1MZ1LDrZcJGcyWCytgjYozVKwxSi6PsEaQ=	3	\N	2026-03-13 00:09:57.336158+02	t	t	t	t	active	مسؤول كلية	{1,2,4,5}	\N	\N
8	omar	omar@gmail.com	pbkdf2_sha256$1000000$vlZHhPpW9IpNAdiVAlRLoZ$EKZZMi53hEdx/k1aLRSkqXWKnmZgVcXUMN0N8tP7RNQ=	1	\N	2025-10-30 01:10:42.356929+03	t	t	t	t	active	مسؤول كلية	{1,2,3,7,6,4,5}	\N	\N
24	culturedept	culturedept@gmail.com	pbkdf2_sha256$1000000$v8zWc4ANZlYIYRwN0tIMwz$IkQybCAsxps7w88JEaz276ucTV2KC9urijBSvwkVCfI=	\N	3	2026-03-13 02:28:35.041691+02	t	t	t	t	active	مدير ادارة	{}	\N	\N
13	string	admin@example.com	pbkdf2_sha256$1000000$QvWcdHW5PZf3birfhgr1K1$ze8CXVUv+iOXUkR+zOGt0dx9HGx9I5Tsl47DoOmL4KY=	\N	\N	2025-11-15 03:30:33.532263+02	t	t	t	t	active	مشرف النظام	{}	\N	\N
5	خالد إبراهيم	khaled.manager@example.com	pbkdf2_sha256$1000000$6rS7AFWRCbRmGf2v87CR0Q$XLigYMDMnB9E0MwVlDgY1YZcxbM3wADe3VuYh1mGxSM=	\N	2	2025-10-20 02:53:23.217139+03	t	t	t	t	active	مدير ادارة	{}	\N	\N
10	A	a@gmail.com	pbkdf2_sha256$1000000$wN2OdjwYyuKZ9kKEjKkhPH$LMzBhFiIGlM6QlllHD9z+PtdJd1aF0hNRQdCTFJgYRY=	\N	\N	2025-10-30 01:37:07.429515+03	t	t	t	t	active	مشرف النظام	{}	\N	\N
20	admin34	admin34@example.com	pbkdf2_sha256$1000000$WqUSKaWUHuPX89VGicr9jA$La3PHY+349r/DeTyaXSvAoO3K3S5JvzcI/I7rq2ltVk=	2	\N	2025-11-21 16:34:27.807083+02	t	t	t	t	active	مدير كلية	{}	\N	\N
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
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
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: clan_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.clan_groups (group_id, name, clan_id, display_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: clans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.clans (clan_id, name, description, faculty_id, created_by, status, min_members, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.departments (dept_id, name, description, created_at, for_env_fam) FROM stdin;
1	إدارة النشاط الثقافي و الفنى	\N	2026-04-16 02:32:54.342517+02	f
2	إدارة النشاط الاجتماعي	\N	2026-04-16 02:32:54.342517+02	f
3	إدارة النشاط الرياضي و الرحلات	\N	2026-04-16 02:32:54.342517+02	f
4	إدارة الأسر الطلابية و الاتحادات	\N	2026-04-16 02:32:54.342517+02	f
5	إدارة النشاط العلمى و التكنولوجي	\N	2026-04-16 02:32:54.342517+02	f
6	إدارة التكافل الاجتماعي	\N	2026-04-16 02:32:54.342517+02	f
7	إدارة الجوالة و الخدمة العامة و المعسكرات	\N	2026-04-16 02:32:54.342517+02	f
8	إدارات فرعيه	\N	2026-04-16 02:32:54.342517+02	f
9	وحدة التنمية البشرية	\N	2026-04-16 02:32:54.342517+02	f
10	وحدة الأنشطة الطلابية الدامجة و المبادرات	\N	2026-04-16 02:32:54.342517+02	f
11	مركز مشروع التشغيل الطلابي	\N	2026-04-16 02:32:54.342517+02	f
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
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
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
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
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documents (doc_id, owner_id, f_name, f_path, f_type, uploaded_at, owner_type) FROM stdin;
\.


--
-- Data for Name: event_docs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_docs (doc_id, event_id, doc_type, file_name, file_path, mime_type, file_size, uploaded_at, uploaded_by) FROM stdin;
17	67	event_image	dog.jpeg	uploads/events/67/dog.jpeg	image/jpeg	83040	2026-03-13 02:31:05.16337+02	24
18	67	event_image	cat.jpg	uploads/events/67/cat.jpg	image/jpeg	141430	2026-03-13 03:06:46.704535+02	24
19	67	event_image	maze simple.png	uploads/events/67/maze simple.png	image/png	804	2026-03-13 03:19:59.79139+02	24
20	66	event_image	dog.jpeg	uploads/events/66/dog.jpeg	image/jpeg	83040	2026-03-13 03:27:04.923681+02	22
21	66	event_image	cat.jpg	uploads/events/66/cat.jpg	image/jpeg	141430	2026-03-13 03:27:07.811385+02	22
22	68	event_image	cat.jpg	uploads/events/68/cat.jpg	image/jpeg	141430	2026-03-13 03:37:32.201121+02	24
23	67	event_image	cat.jpg	uploads/events/67/cat_2ZONWKj.jpg	image/jpeg	141430	2026-03-13 03:39:10.634926+02	24
24	70	event_image	cat.jpg	uploads/events/70/cat.jpg	image/jpeg	141430	2026-03-13 08:49:27.535684+02	22
25	65	event_image	cat.jpg	uploads/events/65/cat.jpg	image/jpeg	141430	2026-03-13 09:19:53.392935+02	22
26	65	event_image	dog.jpeg	uploads/events/65/dog.jpeg	image/jpeg	83040	2026-03-13 09:19:55.873209+02	22
\.


--
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.events (event_id, title, description, dept_id, faculty_id, created_by, updated_at, cost, location, restrictions, reward, status, st_date, end_date, s_limit, created_at, type, family_id, resource, selected_facs, plan_id, active, rejection_reason) FROM stdin;
10	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2026-04-18 07:18:47.280806+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	مقبول	2025-12-07	2025-12-07	100	2025-12-07 17:16:53.936244+02	نشاط ثقافي	4	\N	\N	\N	t	\N
12	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:19:10.52061+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:19:10.520637+02	نشاط ثقافي	4	\N	\N	\N	t	\N
13	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:19:12.852796+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:19:12.85282+02	نشاط ثقافي	4	\N	\N	\N	t	\N
14	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:19:44.659524+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:19:44.659554+02	نشاط ثقافي	4	\N	\N	\N	t	\N
15	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:20:41.032704+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:20:41.032732+02	نشاط ثقافي	4	\N	\N	\N	t	\N
16	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:21:03.009015+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:21:03.009047+02	نشاط ثقافي	4	\N	\N	\N	t	\N
17	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:44:36.565793+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:44:36.565822+02	نشاط ثقافي	4	\N	\N	\N	t	\N
18	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:45:35.736096+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:45:35.736127+02	نشاط ثقافي	4	\N	\N	\N	t	\N
19	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:47:51.603418+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:47:51.603447+02	نشاط ثقافي	4	\N	\N	\N	t	\N
20	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:48:38.107583+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:48:38.107613+02	نشاط ثقافي	4	\N	\N	\N	t	\N
21	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 17:59:21.060944+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 17:59:21.060974+02	نشاط ثقافي	4	\N	\N	\N	t	\N
22	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:00:28.202776+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:00:28.202806+02	نشاط ثقافي	4	\N	\N	\N	t	\N
23	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:01:34.368368+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:01:34.368398+02	نشاط ثقافي	4	\N	\N	\N	t	\N
24	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:05:37.287877+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:05:37.287907+02	نشاط ثقافي	4	\N	\N	\N	t	\N
25	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:07:47.105303+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:07:47.105327+02	نشاط ثقافي	4	\N	\N	\N	t	\N
26	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:10:20.311338+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:10:20.31137+02	نشاط ثقافي	4	\N	\N	\N	t	\N
27	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:12:30.503864+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:12:30.503894+02	نشاط ثقافي	4	\N	\N	\N	t	\N
28	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:19:58.057411+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:19:58.057439+02	نشاط ثقافي	4	\N	\N	\N	t	\N
11	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2026-04-18 07:19:53.202264+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	مرفوض	2025-12-07	2025-12-07	100	2025-12-07 17:18:45.664251+02	نشاط ثقافي	4	\N	\N	\N	t	\N
30	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2025-12-07 18:25:56.956089+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:25:56.956135+02	نشاط ثقافي	4	\N	\N	\N	t	\N
9	مسابقة فنية	مسابقة للانشطة الفنية	\N	\N	5	2026-02-15 16:38:51.967313+02	\N	مصر		شهادة تقدير	مقبول	2025-12-07	2025-12-07	10	2025-12-07 16:56:05.82235+02	نشاط فني	2	\N	\N	\N	f	\N
61	hello world	لننلنلن	\N	1	8	2026-04-19 13:09:03.352982+02	9000.00	string		اتتاتات	موافقة مبدئية	2026-03-10	2026-03-10	10	2026-03-10 02:19:59.264969+02	نشاط فني	\N	\N	\N	1	t	\N
39	ندوة ثقافية حول الأدب العربي	ندوة متخصصة تناقش أهم التطورات في الأدب العربي الحديث	\N	1	1	2026-04-16 02:32:34.578064+02	500.00	قاعة المحاضرات الرئيسية	\N	\N	منتظر	2024-03-15	2024-03-15	\N	2025-12-11 23:34:26.184728+02	اسر	20	\N	\N	\N	t	\N
40	معرض الفنون الشعبية	عرض للفنون الشعبية التقليدية	\N	1	1	2026-04-16 02:32:34.578064+02	1000.00	مركز الفنون	\N	\N	منتظر	2024-04-01	2024-04-03	\N	2025-12-11 23:34:26.187325+02	اسر	20	\N	\N	\N	t	\N
45	حملة تنظيف المجتمع	حملة تطوعية لتنظيف أماكن بيئية حساسة	\N	1	1	2026-04-16 02:32:34.578064+02	400.00	الحي السكني	\N	\N	منتظر	2024-04-20	2024-04-20	\N	2025-12-11 23:34:26.201259+02	اسر	20	\N	\N	\N	t	\N
55	نشاط تبع خطة 2	string	\N	1	1	2026-04-16 02:32:34.578064+02	5000.00	string	string	string	مقبول	2026-02-16	2026-02-16	100	2025-12-12 02:11:20.194955+02	نشاط فني	21	\N	\N	2	t	\N
31	ندوة ثقافية حول الأدب العربي	ندوة متخصصة تناقش أهم التطورات في الأدب العربي الحديث	\N	1	1	2026-04-16 02:32:34.578064+02	500.00	قاعة المحاضرات الرئيسية	\N	\N	منتظر	2024-03-15	2024-03-15	\N	2025-12-11 23:30:45.939607+02	\N	19	\N	\N	\N	t	\N
32	معرض الفنون الشعبية	عرض للفنون الشعبية التقليدية	\N	1	1	2026-04-16 02:32:34.578064+02	1000.00	مركز الفنون	\N	\N	منتظر	2024-04-01	2024-04-03	\N	2025-12-11 23:30:45.945529+02	\N	19	\N	\N	\N	t	\N
8	بطولة كرة القدم الثلاثية	بطولة رياضية لكرة القدم تجمع بين فرق من مختلف الكليات	\N	1	1	2026-04-16 02:32:34.578064+02	40.00	ملعب كرة القدم	يجب أن تكون الفرق من طلاب الجامعة فقط	كأس ودروع تذكارية وشهادات	مقبول	2024-04-20	2024-04-25	180	2025-11-29 18:47:41.600095+02	نشاط رياضي	2	\N	\N	\N	f	\N
5	نشاط تبع خطة 1	string	\N	1	1	2026-04-16 02:32:34.578064+02	5000.00	string	string	string	مقبول	2026-02-16	2026-02-16	100	2025-11-29 18:47:41.600095+02	نشاط فني	2	\N	\N	1	t	\N
37	حملة تنظيف المجتمع	حملة تطوعية لتنظيف أماكن بيئية حساسة	\N	1	1	2026-04-16 02:32:34.578064+02	400.00	الحي السكني	\N	\N	منتظر	2024-04-20	2024-04-20	\N	2025-12-11 23:30:45.960667+02	\N	19	\N	\N	\N	t	\N
47	ندوة ثقافية حول الأدب العربي	ندوة متخصصة تناقش أهم التطورات في الأدب العربي الحديث	\N	1	1	2026-04-16 02:32:34.578064+02	500.00	قاعة المحاضرات الرئيسية	\N	\N	منتظر	2024-03-15	2024-03-15	\N	2025-12-12 00:55:32.047388+02	اسر	21	\N	\N	\N	t	\N
48	معرض الفنون الشعبية	عرض للفنون الشعبية التقليدية	\N	1	1	2026-04-16 02:32:34.578064+02	1000.00	مركز الفنون	\N	\N	منتظر	2024-04-01	2024-04-03	\N	2025-12-12 00:55:32.052484+02	اسر	21	\N	\N	\N	t	\N
53	حملة تنظيف المجتمع	حملة تطوعية لتنظيف أماكن بيئية حساسة	\N	1	1	2026-04-16 02:32:34.578064+02	400.00	الحي السكني	\N	\N	منتظر	2024-04-20	2024-04-20	\N	2025-12-12 00:55:32.073447+02	اسر	21	\N	\N	\N	t	\N
56	string نشاط	string	\N	1	1	2026-04-16 02:32:34.578064+02	62.30	string	string	string	منتظر	2026-02-16	2026-02-16	10	2026-02-17 00:13:05.788776+02	نشاط بيئي	6	\N	\N	\N	t	\N
59	fds	sdgagas	\N	1	8	2026-04-16 02:32:34.578064+02	40.00	sga	gsdga	gsfdgsg	ملغي	2026-03-13	2026-03-20	40	2026-03-06 05:37:19.430602+02	نشاط معسكرات	\N		\N	8	f	\N
60	fds	sdaf	\N	1	8	2026-04-16 02:32:34.578064+02	3.00	dfsa	dfs	dsa	موافقة مبدئية	2026-03-14	2026-03-28	3	2026-03-07 00:32:11.047665+02	نشاط خدمة عامة	\N	dfa	\N	\N	f	\N
29	مسابقة دينية	مسابقة حفظ القران الكريم	\N	1	1	2026-04-16 02:32:34.578064+02	\N	المسجد	ثلاث اجزاء فأعلي	مصحف	منتظر	2025-12-07	2025-12-07	100	2025-12-07 18:21:19.632811+02	نشاط ثقافي	4	\N	\N	\N	t	\N
33	ورشة تصميم الملصقات	تدريب على تصميم ملصقات جذابة	\N	1	1	2026-04-16 02:32:34.578064+02	300.00	قاعة التصميم	\N	\N	منتظر	2024-03-20	2024-03-20	\N	2025-12-11 23:30:45.948323+02	\N	19	\N	\N	\N	t	\N
4	مسابقة الخطابة والإلقاء	مسابقة لاختبار مهارات الخطابة والإلقاء لدى الطلاب	\N	2	1	2026-04-16 02:32:34.578064+02	30.00	الحاضرة الكبرى	يجب أن يكون المشارك متقنًا للغة العربية	جوائز نقدية وشهادات دولية	منتظر	2024-04-05	2024-04-07	120	2025-11-29 18:47:41.600095+02	نشاط ثقافي	1	\N	\N	\N	f	\N
38	بطولة كرة القدم الودية	بطولة ودية بين أسر الجامعة	\N	1	1	2026-04-16 02:32:34.578064+02	1500.00	الملعب الرياضي	\N	\N	منتظر	2024-05-15	2024-05-20	\N	2025-12-11 23:30:45.96406+02	\N	19	\N	\N	\N	t	\N
41	ورشة تصميم الملصقات	تدريب على تصميم ملصقات جذابة	\N	1	1	2026-04-16 02:32:34.578064+02	300.00	قاعة التصميم	\N	\N	منتظر	2024-03-20	2024-03-20	\N	2025-12-11 23:34:26.189949+02	اسر	20	\N	\N	\N	t	\N
46	بطولة كرة القدم الودية	بطولة ودية بين أسر الجامعة	\N	1	1	2026-04-16 02:32:34.578064+02	1500.00	الملعب الرياضي	\N	\N	منتظر	2024-05-15	2024-05-20	\N	2025-12-11 23:34:26.203563+02	اسر	20	\N	\N	\N	t	\N
49	ورشة تصميم الملصقات	تدريب على تصميم ملصقات جذابة	\N	1	1	2026-04-16 02:32:34.578064+02	300.00	قاعة التصميم	\N	\N	منتظر	2024-03-20	2024-03-20	\N	2025-12-12 00:55:32.057477+02	اسر	21	\N	\N	\N	t	\N
54	بطولة كرة القدم الودية	بطولة ودية بين أسر الجامعة	\N	1	1	2026-04-16 02:32:34.578064+02	1500.00	الملعب الرياضي	\N	\N	منتظر	2024-05-15	2024-05-20	\N	2025-12-12 00:55:32.078086+02	اسر	21	\N	\N	\N	t	\N
65	عنوان وهمي	بسيلش	\N	3	22	2026-04-16 02:32:34.578064+02	22.00	يس	لسيلس	يبسبش	مقبول	2026-03-20	2026-03-27	100	2026-03-13 00:28:45.408244+02	داخلي	\N	يسلايبس	\N	\N	t	\N
66	نشاط ثقافي هنعمله	\N	\N	3	22	2026-04-16 02:32:34.578064+02	500.00	عمدهم	\N	\N	ملغي	2026-03-18	2026-04-16	400	2026-03-13 00:30:21.455039+02	داخلي	\N	\N	\N	15	f	\N
70	نشاط ثقافي هنعمله	بسشب	\N	3	22	2026-04-16 02:32:34.578064+02	500.00	عمدهم لل			مقبول	2026-03-18	2026-04-16	400	2026-03-13 00:30:21.455039+02	داخلي	\N		\N	15	f	\N
7	ندوة البحث العلمي	ندوة علمية لمناقشة أحدث الأبحاث العلمية في المجالات المختلفة	\N	3	1	2026-04-16 02:32:34.578064+02	25.00	قاعة المؤتمرات	يفضل أن يكون المشارك من طلاب الدراسات العليا	شهادات حضور وفرص تعاون بحثي	مقبول	2024-05-01	2024-05-02	80	2025-11-29 18:47:41.600095+02	نشاط علمي	2	\N	\N	\N	t	\N
34	رحلة ترفيهية إلى الطبيعة	رحلة جماعية للاستمتاع بالطبيعة	\N	1	1	2026-04-16 02:32:34.578064+02	2000.00	محمية الطبيعة	\N	\N	منتظر	2024-04-10	2024-04-10	\N	2025-12-11 23:30:45.950819+02	\N	19	\N	\N	\N	t	\N
42	رحلة ترفيهية إلى الطبيعة	رحلة جماعية للاستمتاع بالطبيعة	\N	1	1	2026-04-16 02:32:34.578064+02	2000.00	محمية الطبيعة	\N	\N	منتظر	2024-04-10	2024-04-10	\N	2025-12-11 23:34:26.192836+02	اسر	20	\N	\N	\N	t	\N
50	رحلة ترفيهية إلى الطبيعة	رحلة جماعية للاستمتاع بالطبيعة	\N	1	1	2026-04-16 02:32:34.578064+02	2000.00	محمية الطبيعة	\N	\N	منتظر	2024-04-10	2024-04-10	\N	2025-12-12 00:55:32.061811+02	اسر	21	\N	\N	\N	t	\N
6	حملة البيئة النظيفة	حملة تطوعية للحفاظ على نظافة الحرم الجامعي والبيئة المحيطة	\N	1	1	2026-04-16 02:32:34.578064+02	0.00	الحرم الجامعي	يفضل المشاركة في الأنشطة البيئية السابقة	شهادات تطوع وجوائز رمزية	مقبول	2024-03-20	2027-03-21	100	2025-11-29 18:47:41.600095+02	نشاط بيئي	3	\N	\N	1	f	\N
35	ورشة الرسم الحديث	تعليم تقنيات الرسم الحديثة والفن المعاصر	\N	1	1	2026-04-16 02:32:34.578064+02	600.00	معهد الفنون	\N	\N	منتظر	2024-03-25	2024-03-25	\N	2025-12-11 23:30:45.953575+02	\N	19	\N	\N	\N	t	\N
43	ورشة الرسم الحديث	تعليم تقنيات الرسم الحديثة والفن المعاصر	\N	1	1	2026-04-16 02:32:34.578064+02	600.00	معهد الفنون	\N	\N	منتظر	2024-03-25	2024-03-25	\N	2025-12-11 23:34:26.195776+02	اسر	20	\N	\N	\N	t	\N
51	ورشة الرسم الحديث	تعليم تقنيات الرسم الحديثة والفن المعاصر	\N	1	1	2026-04-16 02:32:34.578064+02	600.00	معهد الفنون	\N	\N	منتظر	2024-03-25	2024-03-25	\N	2025-12-12 00:55:32.065461+02	اسر	21	\N	\N	\N	t	\N
36	محاضرة علمية عن الذكاء الاصطناعي	محاضرة عن تطبيقات الذكاء الاصطناعي في العالم الحقيقي	\N	1	1	2026-04-16 02:32:34.578064+02	800.00	مختبر العلوم	\N	\N	منتظر	2024-05-01	2024-05-01	\N	2025-12-11 23:30:45.956916+02	\N	19	\N	\N	\N	t	\N
44	محاضرة علمية عن الذكاء الاصطناعي	محاضرة عن تطبيقات الذكاء الاصطناعي في العالم الحقيقي	\N	1	1	2026-04-16 02:32:34.578064+02	800.00	مختبر العلوم	\N	\N	منتظر	2024-05-01	2024-05-01	\N	2025-12-11 23:34:26.198655+02	اسر	20	\N	\N	\N	t	\N
52	محاضرة علمية عن الذكاء الاصطناعي	محاضرة عن تطبيقات الذكاء الاصطناعي في العالم الحقيقي	\N	\N	1	2026-04-16 02:32:34.578064+02	800.00	مختبر العلوم	\N	\N	منتظر	2024-05-01	2024-05-01	\N	2025-12-12 00:55:32.068857+02	\N	\N	\N	\N	\N	t	\N
58	string	string	\N	1	8	2026-04-16 02:32:34.578064+02	50.00	string	string	string	موافقة مبدئية	2026-03-10	2026-03-10	0	2026-02-23 06:01:32.367746+02	نشاط رياضي	\N	\N	{1,2}	1	t	\N
64	نشاط في نص الترم	ok	\N	3	22	2026-04-16 02:32:34.578064+02	5000.00	عندهم	سبق له ان اشترك في اي نشاط	جايزة	ملغي	2026-03-21	2026-05-07	55	2026-03-13 00:17:54.882452+02	داخلي	\N	دعم مصر	\N	\N	f	\N
71	nvhn	hrttyhyt	2	1	8	2026-04-16 03:00:01.157446+02	665.00	ngngnn			موافقة مبدئية	2026-04-18	2026-04-18	100	2026-04-16 03:00:01.15752+02	داخلي	\N		\N	\N	f	\N
62	string	\N	\N	1	8	2026-04-17 02:01:24.210439+02	6095.00	string	\N	\N	مقبول	2026-03-25	2027-03-11	0	2026-03-11 19:30:39.412878+02	داخلي	\N	\N	\N	1	t	\N
63	string	string	\N	1	8	2026-04-17 02:01:34.408935+02	9.00	string	string	string	مرفوض	2026-03-11	2026-03-11	0	2026-03-11 19:31:30.730013+02	داخلي	\N	\N	\N	1	t	\N
68	بيس		3	\N	24	2026-04-17 04:06:03.751371+02	5.00	لسي			مقبول	2026-03-20	2026-04-02	5	2026-03-13 03:37:06.978294+02	خارجي	\N	\N	{3,2,1}	16	t	\N
67	ثقافة مصر	ليسsa	1	\N	24	2026-04-17 04:06:03.751371+02	4000.00	عند الشعار	لسلس	ليس	مقبول	2025-12-25	2026-01-08	500	2026-03-13 02:30:29.900973+02	خارجي	\N	ليسل	{3,2,1}	\N	f	\N
3	ماراثون العدو السنوي	فعالية رياضية سنوية تجمع طلاب الجامعة للمشاركة في ماراثون العدو	3	1	1	2026-04-18 05:52:21.757849+02	50.00	الملعب الرياضي	يجب أن يكون المشارك طالباً حالياً بالجامعة	جوائز نقدية وشهادات تقدير	ملغي	2024-03-15	2026-03-30	200	2025-11-29 18:47:41.600095+02	نشاط رياضي	\N	\N	\N	\N	f	\N
73	test rejection	gdogh;spadghgapsugas[hgh[sofdapg	2	1	8	2026-04-29 00:18:32.966793+03	200.00	HU			موافقة مبدئية	2026-04-30	2026-05-09	100	2026-04-29 00:18:32.966826+03	داخلي	\N		\N	\N	f	\N
72	spp	sfdsgsagasasg	3	\N	24	2026-04-29 00:27:34.809309+03	12.00	sss			مرفوض	2026-04-30	2026-05-07	100	2026-04-25 04:22:29.705983+03	خارجي	\N		{2,3,1}	\N	f	not supported
74	معرض	\N	\N	1	8	2026-05-08 02:19:01.414185+03	505050.00	يسلشلي	\N	\N	منتظر	2026-05-15	2026-05-22	505	2026-05-08 02:19:01.414222+03	داخلي	\N	\N	\N	11	f	\N
75	المرعض	\N	\N	2	24	2026-05-09 01:40:49.335078+03	10.00	سشيسش	\N	\N	مرفوض	2026-05-20	2026-06-04	50	2026-05-08 02:22:05.807349+03	خارجي	\N	\N	\N	16	f	non
\.


--
-- Data for Name: faculties; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.faculties (faculty_id, name, major, created_at, aff_discount, reg_discount, bk_discount, full_discount) FROM stdin;
2	كلية العلوم	{"علوم أساسية"}	2025-10-20 02:34:30.31113+03	{400}	{300}	{200}	{100}
3	الطب	{البشري}	2025-10-25 22:28:16.437365+03	{100}	{200,500}	{300}	{400}
1	كلية الهندسة	{"هندسة عامة"}	2025-10-20 02:34:30.31113+03	{100,200}	{50}	{500,600}	{1020}
\.


--
-- Data for Name: families; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.families (family_id, name, description, faculty_id, created_by, approved_by, status, created_at, updated_at, min_limit, type, closing_date) FROM stdin;
1	أسرة نوعية	أسرة نوعية متخصصة في الأنشطة الرياضية والثقافية	1	1	1	موافقة مبدئية	2025-11-29 18:30:42.982008+02	2026-02-16 20:47:40.316478+02	100	نوعية	2025-12-14
2	أسرة مركزية	أسرة مركزية على مستوى الجامعة غير مرتبطة بكلية معينة	\N	1	10	موافقة مبدئية	2025-11-29 18:30:42.982008+02	2026-02-16 20:47:40.316478+02	100	مركزية	2025-01-01
3	أصدقاء البيئة	أسرة متخصصة في الأنشطة البيئية والاستدامة	1	1	16	مقبول	2025-11-29 18:30:42.982008+02	2026-02-16 21:28:38.043754+02	100	اصدقاء البيئة	2025-01-01
4	نادي الرياضة	أسرة متخصصة في الأنشطة الرياضية والنشاط البدني	1	1	\N	مرفوض	2025-12-06 23:12:48.322738+02	2025-12-14 17:44:27.358042+02	50	نوعية	2025-01-01
6	نادي الرياضة	أسرة متخصصة في الأنشطة الرياضية والنشاط البدني	1	1	\N	موافقة مبدئية	2025-12-06 23:30:14.220471+02	2026-02-16 20:28:55.748327+02	15	نوعية	2025-01-01
5	نادي الرياضة	أسرة متخصصة في الأنشطة الرياضية والنشاط البدني	1	1	\N	موافقة مبدئية	2025-12-06 23:22:21.065725+02	2026-02-16 20:29:42.682564+02	50	نوعية	2025-01-01
20	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	مقبول	2025-12-11 23:34:26.155704+02	2026-02-16 21:24:19.152637+02	20	نوعية	\N
14	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-11 23:13:26.605204+02	2025-12-12 21:21:53.420012+02	20	نوعية	\N
19	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-11 23:30:45.911519+02	2025-12-12 21:21:53.420012+02	20	نوعية	\N
21	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	موافقة مبدئية	2025-12-12 00:55:32.002298+02	2025-12-12 21:21:53.420012+02	15	نوعية	\N
16	أسرة الإبداع والفنون	أسرة متخصصة في الأنشطة الإبداعية والفنية لتنمية مهارات الطلاب	1	1	\N	منتظر	2025-12-11 23:16:04.293144+02	2026-04-18 07:25:35.042203+02	20	نوعية	\N
\.


--
-- Data for Name: family_admins; Type: TABLE DATA; Schema: public; Owner: -
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
-- Data for Name: family_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.family_members (family_id, student_id, role, status, joined_at, dept_id) FROM stdin;
2	41	عضو	منتظر	2026-04-19 12:51:43.94184+02	\N
3	20	أخت كبرى	مرفوض	2025-11-29 18:35:41.878043+02	\N
3	22	عضو	مقبول	2025-11-29 18:35:41.878043+02	\N
3	16	عضو	مقبول	2025-11-29 18:35:41.878043+02	\N
3	21	عضو	موافقة مبدئية	2025-11-29 18:35:41.878043+02	\N
3	11	عضو	مقبول	2025-12-06 22:42:57.139362+02	\N
3	13	عضو	مرفوض	2026-02-16 21:28:55.115167+02	\N
2	16	أخت كبرى	منتظر	2025-11-29 18:35:41.878043+02	\N
4	22	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.338154+02	\N
4	34	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.338532+02	\N
4	1	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.339141+02	\N
4	35	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.339442+02	\N
4	36	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.339764+02	\N
4	28	أمين مساعد لجنة	منتظر	2025-12-06 23:12:48.340044+02	\N
5	22	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.074009+02	\N
5	34	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.074268+02	\N
5	1	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.074852+02	\N
5	35	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.075165+02	\N
5	36	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.075487+02	\N
5	28	أمين مساعد لجنة	منتظر	2025-12-06 23:22:21.075823+02	\N
6	22	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.22938+02	\N
6	34	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.229667+02	\N
6	1	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.230245+02	\N
6	35	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.230509+02	\N
6	36	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.230768+02	\N
6	28	أمين مساعد لجنة	منتظر	2025-12-06 23:30:14.231031+02	\N
2	18	عضو	منتظر	2025-11-29 18:35:41.878043+02	\N
2	11	عضو	منتظر	2025-11-29 18:35:41.878043+02	\N
1	13	عضو	منتظر	2025-11-29 18:35:41.878043+02	\N
3	19	أخ أكبر	مقبول	2025-11-29 18:35:41.878043+02	\N
5	13	عضو	منتظر	2026-02-16 21:28:04.16266+02	\N
6	13	أخ أكبر	مقبول	2025-12-06 23:30:14.225358+02	\N
4	16	أمين لجنة	منتظر	2025-12-06 23:12:48.335907+02	\N
4	18	أمين لجنة	منتظر	2025-12-06 23:12:48.336729+02	\N
4	19	أمين لجنة	منتظر	2025-12-06 23:12:48.33714+02	\N
4	20	أمين لجنة	منتظر	2025-12-06 23:12:48.33749+02	\N
4	21	أمين لجنة	منتظر	2025-12-06 23:12:48.337833+02	\N
5	16	أمين لجنة	منتظر	2025-12-06 23:22:21.072099+02	\N
5	18	أمين لجنة	منتظر	2025-12-06 23:22:21.072812+02	\N
5	19	أمين لجنة	منتظر	2025-12-06 23:22:21.073167+02	\N
5	20	أمين لجنة	منتظر	2025-12-06 23:22:21.073458+02	\N
5	21	أمين لجنة	منتظر	2025-12-06 23:22:21.073746+02	\N
6	16	أمين لجنة	منتظر	2025-12-06 23:30:14.22727+02	\N
6	18	أمين لجنة	منتظر	2025-12-06 23:30:14.228077+02	\N
6	19	أمين لجنة	منتظر	2025-12-06 23:30:14.22845+02	\N
6	20	أمين لجنة	منتظر	2025-12-06 23:30:14.228771+02	\N
6	21	أمين لجنة	منتظر	2025-12-06 23:30:14.229093+02	\N
1	11	أخ أكبر	منتظر	2025-11-29 18:35:41.878043+02	\N
4	11	أخ أكبر	منتظر	2025-12-06 23:12:48.334231+02	\N
5	11	أخ أكبر	منتظر	2025-12-06 23:22:21.070555+02	\N
14	18	أخت كبرى	منتظر	2025-12-11 23:13:26.620967+02	\N
14	29	أمين سر	منتظر	2025-12-11 23:13:26.623685+02	\N
14	36	عضو منتخب	منتظر	2025-12-11 23:13:26.626447+02	\N
14	13	عضو منتخب	منتظر	2025-12-11 23:13:26.62934+02	\N
14	22	أمين لجنة	منتظر	2025-12-11 23:13:26.63106+02	\N
14	1	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.631554+02	\N
14	11	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.633565+02	\N
14	35	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.635391+02	\N
14	20	أمين لجنة	منتظر	2025-12-11 23:13:26.636874+02	\N
14	21	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.637157+02	\N
14	28	أمين لجنة	منتظر	2025-12-11 23:13:26.638601+02	\N
14	34	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.638879+02	\N
14	2	أمين لجنة	منتظر	2025-12-11 23:13:26.640341+02	\N
14	16	أمين لجنة	منتظر	2025-12-11 23:13:26.642112+02	\N
14	19	أمين مساعد لجنة	منتظر	2025-12-11 23:13:26.64242+02	\N
16	18	أخت كبرى	منتظر	2025-12-11 23:16:04.3069+02	\N
16	29	أمين سر	منتظر	2025-12-11 23:16:04.309537+02	\N
16	36	عضو منتخب	منتظر	2025-12-11 23:16:04.31212+02	\N
16	13	عضو منتخب	منتظر	2025-12-11 23:16:04.314664+02	\N
16	22	أمين لجنة	منتظر	2025-12-11 23:16:04.316225+02	\N
16	1	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.316632+02	\N
16	11	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.318438+02	\N
16	35	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.320193+02	\N
16	20	أمين لجنة	منتظر	2025-12-11 23:16:04.321799+02	\N
16	21	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.322166+02	\N
16	28	أمين لجنة	منتظر	2025-12-11 23:16:04.323732+02	\N
16	34	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.324023+02	\N
16	2	أمين لجنة	منتظر	2025-12-11 23:16:04.325461+02	\N
16	16	أمين لجنة	منتظر	2025-12-11 23:16:04.3272+02	\N
16	19	أمين مساعد لجنة	منتظر	2025-12-11 23:16:04.327471+02	\N
19	18	أخت كبرى	منتظر	2025-12-11 23:30:45.928583+02	\N
19	29	أمين سر	منتظر	2025-12-11 23:30:45.931432+02	\N
19	36	عضو منتخب	منتظر	2025-12-11 23:30:45.934086+02	\N
19	22	أمين لجنة	منتظر	2025-12-11 23:30:45.938712+02	\N
19	1	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.939134+02	\N
19	11	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.947971+02	\N
19	35	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.950474+02	\N
19	20	أمين لجنة	منتظر	2025-12-11 23:30:45.952963+02	\N
19	21	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.953251+02	\N
19	28	أمين لجنة	منتظر	2025-12-11 23:30:45.956106+02	\N
19	34	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.956415+02	\N
19	2	أمين لجنة	منتظر	2025-12-11 23:30:45.959918+02	\N
19	16	أمين لجنة	منتظر	2025-12-11 23:30:45.962716+02	\N
19	19	أمين مساعد لجنة	منتظر	2025-12-11 23:30:45.962996+02	\N
20	18	أخت كبرى	منتظر	2025-12-11 23:34:26.172512+02	\N
20	29	أمين سر	منتظر	2025-12-11 23:34:26.175937+02	\N
20	36	عضو منتخب	منتظر	2025-12-11 23:34:26.179042+02	\N
20	22	أمين لجنة	منتظر	2025-12-11 23:34:26.18379+02	\N
20	1	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.184247+02	\N
20	11	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.189595+02	\N
20	35	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.192458+02	\N
20	20	أمين لجنة	منتظر	2025-12-11 23:34:26.194989+02	\N
20	21	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.195347+02	\N
20	28	أمين لجنة	منتظر	2025-12-11 23:34:26.197993+02	\N
20	34	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.19831+02	\N
20	2	أمين لجنة	منتظر	2025-12-11 23:34:26.200643+02	\N
20	16	أمين لجنة	منتظر	2025-12-11 23:34:26.20295+02	\N
20	19	أمين مساعد لجنة	منتظر	2025-12-11 23:34:26.203236+02	\N
21	18	أخت كبرى	منتظر	2025-12-12 00:55:32.028676+02	\N
21	29	أمين سر	منتظر	2025-12-12 00:55:32.03241+02	\N
21	36	عضو منتخب	منتظر	2025-12-12 00:55:32.037065+02	\N
21	22	أمين لجنة	منتظر	2025-12-12 00:55:32.045295+02	\N
21	1	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.046602+02	\N
21	11	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.056726+02	\N
21	35	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.061121+02	\N
21	20	أمين لجنة	منتظر	2025-12-12 00:55:32.064671+02	\N
21	21	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.065059+02	\N
21	28	أمين لجنة	منتظر	2025-12-12 00:55:32.067986+02	\N
21	34	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.068406+02	\N
21	2	أمين لجنة	منتظر	2025-12-12 00:55:32.072529+02	\N
21	16	أمين لجنة	منتظر	2025-12-12 00:55:32.076667+02	\N
21	19	أمين مساعد لجنة	منتظر	2025-12-12 00:55:32.077141+02	\N
2	13	عضو	مرفوض	2026-02-16 21:08:48.870811+02	\N
21	13	عضو	منتظر	2026-03-11 20:14:06.879268+02	\N
\.


--
-- Data for Name: logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.logs (log_id, actor_id, action, event_id, solidarity_id, family_id, ip_address, logged_at, actor_type, target_type, student_id) FROM stdin;
261	8	انشاء نشاط	71	\N	\N	::1	2026-04-16 03:00:01.158133+02	\N	نشاط	\N
262	8	إنشاء نشاط	71	\N	\N	127.0.0.1	2026-04-16 03:00:01.158133+02	مسؤول كلية	نشاط	\N
263	4	الموافقة على نشاط: string	62	\N	\N	127.0.0.1	2026-04-17 02:01:24.210439+02	مدير كلية	نشاط	\N
264	4	رفض نشاط: string	63	\N	\N	127.0.0.1	2026-04-17 02:01:34.408935+02	مدير كلية	نشاط	\N
265	11	موافقة طلب	\N	45	\N	::1	2026-04-18 01:30:55.658484+02	مشرف النظام	تكافل	\N
266	11	موافقة مشرف النظام على طلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 01:30:55.658484+02	مشرف النظام	تكافل	\N
267	11	رفض طلب	\N	45	\N	::1	2026-04-18 01:31:00.05362+02	مشرف النظام	تكافل	\N
268	11	رفض مشرف النظام لطلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 01:31:00.05362+02	مشرف النظام	تكافل	\N
269	11	رفض طلب	\N	46	\N	::1	2026-04-18 01:42:13.275518+02	مشرف النظام	تكافل	\N
270	11	رفض مشرف النظام لطلب تكافل	\N	46	\N	127.0.0.1	2026-04-18 01:42:13.275518+02	مشرف النظام	تكافل	\N
271	11	رفض طلب	\N	1	\N	::1	2026-04-18 01:50:30.343107+02	مشرف النظام	تكافل	\N
272	11	رفض مشرف النظام لطلب تكافل	\N	1	\N	127.0.0.1	2026-04-18 01:50:30.343107+02	مشرف النظام	تكافل	\N
273	11	موافقة طلب	\N	45	\N	::1	2026-04-18 03:37:12.599069+02	مشرف النظام	تكافل	\N
274	11	موافقة مشرف النظام على طلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 03:37:12.599069+02	مشرف النظام	تكافل	\N
275	11	رفض طلب	\N	45	\N	::1	2026-04-18 03:38:36.904778+02	مشرف النظام	تكافل	\N
276	11	رفض مشرف النظام لطلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 03:38:36.904778+02	مشرف النظام	تكافل	\N
277	11	موافقة طلب	\N	45	\N	::1	2026-04-18 03:38:38.982757+02	مشرف النظام	تكافل	\N
278	11	موافقة مشرف النظام على طلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 03:38:38.982757+02	مشرف النظام	تكافل	\N
279	11	رفض طلب	\N	45	\N	::1	2026-04-18 03:38:41.485876+02	مشرف النظام	تكافل	\N
280	11	رفض مشرف النظام لطلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 03:38:41.485876+02	مشرف النظام	تكافل	\N
281	11	موافقة طلب	\N	45	\N	::1	2026-04-18 03:38:44.889077+02	مشرف النظام	تكافل	\N
282	11	موافقة مشرف النظام على طلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 03:38:44.889077+02	مشرف النظام	تكافل	\N
283	11	رفض طلب	\N	45	\N	::1	2026-04-18 03:38:47.802861+02	مشرف النظام	تكافل	\N
284	11	رفض مشرف النظام لطلب تكافل	\N	45	\N	127.0.0.1	2026-04-18 03:38:47.802861+02	مشرف النظام	تكافل	\N
285	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 03:49:08.021969+02	مدير ادارة	نشاط	\N
286	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 03:49:08.108534+02	مدير ادارة	نشاط	\N
287	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:45:51.002646+02	مدير ادارة	نشاط	\N
288	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:45:51.085612+02	مدير ادارة	نشاط	\N
289	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:48:07.927551+02	مدير ادارة	نشاط	\N
290	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:48:08.021445+02	مدير ادارة	نشاط	\N
291	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:48:35.214776+02	مدير ادارة	نشاط	\N
292	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:48:35.409355+02	مدير ادارة	نشاط	\N
293	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:48:48.826533+02	مدير ادارة	نشاط	\N
294	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:48:48.922158+02	مدير ادارة	نشاط	\N
295	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:49:37.792175+02	مدير ادارة	نشاط	\N
296	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:49:37.866928+02	مدير ادارة	نشاط	\N
297	24	عرض صور النشاط: ماراثون العدو السنوي	3	\N	\N	127.0.0.1	2026-04-18 05:52:34.681269+02	مدير ادارة	نشاط	\N
298	24	عرض صور النشاط: ماراثون العدو السنوي	3	\N	\N	127.0.0.1	2026-04-18 05:52:34.776537+02	مدير ادارة	نشاط	\N
299	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:54:58.924701+02	مدير ادارة	نشاط	\N
300	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:54:59.102638+02	مدير ادارة	نشاط	\N
301	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:56:07.625997+02	مدير ادارة	نشاط	\N
302	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 05:56:07.701784+02	مدير ادارة	نشاط	\N
303	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-18 06:40:14.300934+02	مسؤول كلية	نشاط	\N
304	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-18 06:40:14.566682+02	مسؤول كلية	نشاط	\N
305	24	عرض صور النشاط: ماراثون العدو السنوي	3	\N	\N	127.0.0.1	2026-04-18 06:55:18.52463+02	مدير ادارة	نشاط	\N
306	24	عرض صور النشاط: ماراثون العدو السنوي	3	\N	\N	127.0.0.1	2026-04-18 06:55:18.608778+02	مدير ادارة	نشاط	\N
307	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 07:00:27.134606+02	مدير ادارة	نشاط	\N
308	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 07:00:27.233757+02	مدير ادارة	نشاط	\N
309	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 07:00:39.217525+02	مدير ادارة	نشاط	\N
310	24	عرض صور النشاط: بيس	68	\N	\N	127.0.0.1	2026-04-18 07:00:39.306374+02	مدير ادارة	نشاط	\N
311	24	عرض صور النشاط: ماراثون العدو السنوي	3	\N	\N	127.0.0.1	2026-04-18 07:00:59.233637+02	مدير ادارة	نشاط	\N
312	24	عرض صور النشاط: ماراثون العدو السنوي	3	\N	\N	127.0.0.1	2026-04-18 07:00:59.40723+02	مدير ادارة	نشاط	\N
313	8	الموافقة على نشاط: مسابقة دينية	10	\N	\N	127.0.0.1	2026-04-18 07:18:47.280806+02	مسؤول كلية	نشاط	\N
314	8	رفض نشاط: مسابقة دينية	11	\N	\N	127.0.0.1	2026-04-18 07:19:53.202264+02	مسؤول كلية	نشاط	\N
315	8	تحديث خصومات الكلية: كلية الهندسة	\N	\N	\N	127.0.0.1	2026-04-18 09:14:53.153272+02	مسؤول كلية	اخر	\N
316	8	تحديث خصومات الكلية: كلية الهندسة	\N	\N	\N	127.0.0.1	2026-04-18 09:26:56.825976+02	مسؤول كلية	اخر	\N
319	8	تحديث خصومات الكلية: كلية الهندسة	\N	\N	\N	127.0.0.1	2026-04-19 12:45:20.822703+02	مسؤول كلية	اخر	\N
322	8	منح صلاحية إنشاء أسرة للطالب	\N	\N	\N	127.0.0.1	2026-04-19 12:55:36.869405+02	مسؤول كلية	طالب	41
323	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-19 13:03:58.063472+02	مسؤول كلية	نشاط	\N
324	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-19 13:03:58.170164+02	مسؤول كلية	نشاط	\N
325	8	إضافة نشاط "hello world" إلى الخطة "العام الدراسي 2025-2026"	61	\N	\N	\N	2026-04-19 13:09:03.374536+02	مسؤول كلية	نشاط	\N
326	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-19 13:09:37.791568+02	مسؤول كلية	نشاط	\N
327	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-19 13:09:37.897886+02	مسؤول كلية	نشاط	\N
328	11	موافقة طلب	\N	46	\N	::1	2026-04-19 13:29:38.22503+02	مشرف النظام	تكافل	\N
329	8	عرض مستندات الطلب	\N	45	\N	127.0.0.1	2026-04-19 13:32:57.090895+02	مسؤول كلية	تكافل	\N
330	8	عرض مستندات الطلب	\N	45	\N	127.0.0.1	2026-04-19 13:32:57.197294+02	مسؤول كلية	تكافل	\N
317	8	عرض مستندات الطلب	\N	\N	\N	127.0.0.1	2026-04-19 12:44:35.266778+02	مسؤول كلية	تكافل	\N
318	8	عرض مستندات الطلب	\N	\N	\N	127.0.0.1	2026-04-19 12:44:35.382376+02	مسؤول كلية	تكافل	\N
320	8	عرض مستندات الطلب	\N	\N	\N	127.0.0.1	2026-04-19 12:45:29.64835+02	مسؤول كلية	تكافل	\N
321	8	عرض مستندات الطلب	\N	\N	\N	127.0.0.1	2026-04-19 12:45:29.765892+02	مسؤول كلية	تكافل	\N
331	8	عرض مستندات الطلب	\N	\N	\N	127.0.0.1	2026-04-24 15:18:12.053451+03	مسؤول كلية	تكافل	\N
332	8	عرض مستندات الطلب	\N	\N	\N	127.0.0.1	2026-04-24 15:18:12.23079+03	مسؤول كلية	تكافل	\N
333	24	انشاء نشاط	72	\N	\N	::1	2026-04-25 04:22:29.706226+03	\N	نشاط	\N
334	24	إنشاء نشاط	72	\N	\N	127.0.0.1	2026-04-25 04:22:29.706226+03	مدير ادارة	نشاط	\N
335	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-28 17:33:49.714374+03	مسؤول كلية	نشاط	\N
336	8	عرض صور النشاط: nvhn	71	\N	\N	127.0.0.1	2026-04-28 17:33:49.77956+03	مسؤول كلية	نشاط	\N
337	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 17:38:26.530853+03	مسؤول كلية	تكافل	\N
338	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 17:38:26.58097+03	مسؤول كلية	تكافل	\N
339	8	عرض صور النشاط: ثقافة مصر	67	\N	\N	127.0.0.1	2026-04-28 22:56:55.846725+03	مسؤول كلية	نشاط	\N
340	8	عرض صور النشاط: ثقافة مصر	67	\N	\N	127.0.0.1	2026-04-28 22:56:55.992759+03	مسؤول كلية	نشاط	\N
341	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:00:33.125977+03	مسؤول كلية	تكافل	\N
342	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:00:33.213763+03	مسؤول كلية	تكافل	\N
343	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:00:59.948655+03	مسؤول كلية	تكافل	\N
344	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:01:00.051487+03	مسؤول كلية	تكافل	\N
345	8	عرض مستندات الطلب	\N	45	\N	127.0.0.1	2026-04-28 23:01:03.00613+03	مسؤول كلية	تكافل	\N
346	8	عرض مستندات الطلب	\N	45	\N	127.0.0.1	2026-04-28 23:01:03.22464+03	مسؤول كلية	تكافل	\N
347	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2026-04-28 23:02:30.223368+03	مسؤول كلية	تكافل	\N
348	8	عرض مستندات الطلب	\N	27	\N	127.0.0.1	2026-04-28 23:02:30.310534+03	مسؤول كلية	تكافل	\N
349	8	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2026-04-28 23:03:01.665375+03	مسؤول كلية	تكافل	\N
350	8	عرض مستندات الطلب	\N	26	\N	127.0.0.1	2026-04-28 23:03:01.796883+03	مسؤول كلية	تكافل	\N
351	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:29:21.566823+03	مسؤول كلية	تكافل	\N
352	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:29:21.641091+03	مسؤول كلية	تكافل	\N
353	8	عرض مستندات الطلب	\N	45	\N	127.0.0.1	2026-04-28 23:29:41.521394+03	مسؤول كلية	تكافل	\N
354	8	عرض مستندات الطلب	\N	45	\N	127.0.0.1	2026-04-28 23:29:41.602007+03	مسؤول كلية	تكافل	\N
355	8	عرض مستندات الطلب	\N	45	\N	127.0.0.1	2026-04-28 23:31:13.339256+03	مسؤول كلية	تكافل	\N
356	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:31:14.643795+03	مسؤول كلية	تكافل	\N
357	8	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-04-28 23:31:14.8115+03	مسؤول كلية	تكافل	\N
358	8	انشاء نشاط	73	\N	\N	::1	2026-04-29 00:18:32.967073+03	\N	نشاط	\N
359	8	إنشاء نشاط	73	\N	\N	127.0.0.1	2026-04-29 00:18:32.967073+03	مسؤول كلية	نشاط	\N
360	8	عرض صور النشاط: test rejection	73	\N	\N	127.0.0.1	2026-04-29 00:18:48.587909+03	مسؤول كلية	نشاط	\N
361	8	عرض صور النشاط: test rejection	73	\N	\N	127.0.0.1	2026-04-29 00:18:48.691774+03	مسؤول كلية	نشاط	\N
362	8	عرض صور النشاط: test rejection	73	\N	\N	127.0.0.1	2026-04-29 00:19:09.665743+03	مسؤول كلية	نشاط	\N
363	8	عرض صور النشاط: test rejection	73	\N	\N	127.0.0.1	2026-04-29 00:19:09.83813+03	مسؤول كلية	نشاط	\N
364	6	رفض نشاط: spp	72	\N	\N	127.0.0.1	2026-04-29 00:27:34.809309+03	مدير عام	نشاط	\N
365	10	رفض طلب	\N	18	\N	::1	2026-04-29 00:58:48.828742+03	مشرف النظام	تكافل	\N
366	10	رفض مشرف النظام لطلب تكافل	\N	18	\N	127.0.0.1	2026-04-29 00:58:48.828742+03	مشرف النظام	تكافل	\N
367	10	رفض طلب	\N	47	\N	::1	2026-04-29 00:59:12.512028+03	مشرف النظام	تكافل	\N
368	10	رفض مشرف النظام لطلب تكافل	\N	47	\N	127.0.0.1	2026-04-29 00:59:12.512028+03	مشرف النظام	تكافل	\N
369	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:50:30.622615+03	مسؤول كلية	تكافل	\N
370	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:50:30.895581+03	مسؤول كلية	تكافل	\N
371	17	موافقة مبدئية	\N	17	\N	::1	2026-05-07 22:50:32.895963+03	مسؤول كلية	تكافل	\N
372	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:50:33.075131+03	مسؤول كلية	تكافل	\N
373	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:50:33.580704+03	مسؤول كلية	تكافل	\N
374	17	موافقة طلب	\N	17	\N	::1	2026-05-07 22:50:36.867558+03	مسؤول كلية	تكافل	\N
375	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:50:37.024172+03	مسؤول كلية	تكافل	\N
376	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:50:37.465132+03	مسؤول كلية	تكافل	\N
377	10	رفض طلب	\N	17	\N	::1	2026-05-07 22:52:28.118418+03	مشرف النظام	تكافل	\N
378	10	رفض مشرف النظام لطلب تكافل	\N	17	\N	127.0.0.1	2026-05-07 22:52:28.118418+03	مشرف النظام	تكافل	\N
379	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:55:48.089937+03	مسؤول كلية	تكافل	\N
380	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:55:48.35016+03	مسؤول كلية	تكافل	\N
381	17	موافقة مبدئية	\N	17	\N	::1	2026-05-07 22:56:03.115998+03	مسؤول كلية	تكافل	\N
382	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:03.174131+03	مسؤول كلية	تكافل	\N
383	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:03.722952+03	مسؤول كلية	تكافل	\N
384	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:12.275935+03	مسؤول كلية	تكافل	\N
385	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:12.360791+03	مسؤول كلية	تكافل	\N
386	17	موافقة طلب	\N	17	\N	::1	2026-05-07 22:56:22.289496+03	مسؤول كلية	تكافل	\N
387	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:22.356016+03	مسؤول كلية	تكافل	\N
388	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:22.886487+03	مسؤول كلية	تكافل	\N
389	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:27.997334+03	مسؤول كلية	تكافل	\N
390	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:28.086091+03	مسؤول كلية	تكافل	\N
391	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:50.611042+03	مسؤول كلية	تكافل	\N
392	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:56:50.686161+03	مسؤول كلية	تكافل	\N
393	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:59:39.841437+03	مسؤول كلية	تكافل	\N
394	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:59:40.018724+03	مسؤول كلية	تكافل	\N
395	17	موافقة مبدئية	\N	17	\N	::1	2026-05-07 22:59:41.989714+03	مسؤول كلية	تكافل	\N
396	17	الموافقة المبدئية على طلب التكافل	\N	17	\N	127.0.0.1	2026-05-07 22:59:41.989714+03	مسؤول كلية	تكافل	\N
397	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:59:42.047433+03	مسؤول كلية	تكافل	\N
398	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:59:42.557866+03	مسؤول كلية	تكافل	\N
399	17	تعيين خصومات للطلب - المبلغ الإجمالي: 200.0	\N	17	\N	127.0.0.1	2026-05-07 22:59:47.765878+03	مسؤول كلية	تكافل	\N
400	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:59:47.932603+03	مسؤول كلية	تكافل	\N
401	17	موافقة طلب	\N	17	\N	::1	2026-05-07 22:59:49.32809+03	مسؤول كلية	تكافل	\N
402	17	الموافقة على طلب التكافل	\N	17	\N	127.0.0.1	2026-05-07 22:59:49.32809+03	مسؤول كلية	تكافل	\N
403	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:59:49.382658+03	مسؤول كلية	تكافل	\N
404	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-07 22:59:49.825263+03	مسؤول كلية	تكافل	\N
405	10	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-05-07 23:50:14.526795+03	مشرف النظام	تكافل	\N
406	10	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-05-07 23:50:14.696577+03	مشرف النظام	تكافل	\N
407	10	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2026-05-07 23:53:39.701037+03	مشرف النظام	تكافل	\N
408	10	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2026-05-07 23:53:39.755998+03	مشرف النظام	تكافل	\N
409	10	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2026-05-07 23:54:33.625594+03	مشرف النظام	تكافل	\N
410	10	عرض مستندات الطلب	\N	28	\N	127.0.0.1	2026-05-07 23:54:33.693441+03	مشرف النظام	تكافل	\N
411	10	عرض مستندات الطلب	\N	47	\N	127.0.0.1	2026-05-07 23:55:18.26474+03	مشرف النظام	تكافل	\N
412	10	عرض مستندات الطلب	\N	47	\N	127.0.0.1	2026-05-07 23:55:18.330708+03	مشرف النظام	تكافل	\N
413	10	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-05-07 23:55:57.182996+03	مشرف النظام	تكافل	\N
414	10	عرض مستندات الطلب	\N	46	\N	127.0.0.1	2026-05-07 23:55:57.248581+03	مشرف النظام	تكافل	\N
415	10	عرض مستندات الطلب	\N	18	\N	127.0.0.1	2026-05-07 23:58:26.4621+03	مشرف النظام	تكافل	\N
416	10	عرض مستندات الطلب	\N	18	\N	127.0.0.1	2026-05-07 23:58:26.526354+03	مشرف النظام	تكافل	\N
417	10	عرض مستندات الطلب	\N	18	\N	127.0.0.1	2026-05-07 23:58:56.79758+03	مشرف النظام	تكافل	\N
418	10	عرض مستندات الطلب	\N	18	\N	127.0.0.1	2026-05-07 23:58:56.961931+03	مشرف النظام	تكافل	\N
419	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 00:51:42.450456+03	مسؤول كلية	تكافل	\N
420	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 00:51:42.580198+03	مسؤول كلية	تكافل	\N
421	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 00:54:40.472453+03	مسؤول كلية	تكافل	\N
422	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 00:54:48.331803+03	مسؤول كلية	تكافل	\N
423	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 00:54:51.392838+03	مسؤول كلية	تكافل	\N
424	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:28:01.943142+03	مسؤول كلية	تكافل	\N
425	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:28:02.064883+03	مسؤول كلية	تكافل	\N
426	17	الموافقة المبدئية على طلب التكافل	\N	17	\N	127.0.0.1	2026-05-08 01:28:06.871797+03	مسؤول كلية	تكافل	\N
427	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:28:06.932941+03	مسؤول كلية	تكافل	\N
428	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:28:07.476915+03	مسؤول كلية	تكافل	\N
429	17	تعيين خصومات للطلب - المبلغ الإجمالي: 600.0	\N	17	\N	127.0.0.1	2026-05-08 01:28:13.629967+03	مسؤول كلية	تكافل	\N
430	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:28:13.78905+03	مسؤول كلية	تكافل	\N
431	17	الموافقة على طلب التكافل	\N	17	\N	127.0.0.1	2026-05-08 01:28:27.093658+03	مسؤول كلية	تكافل	\N
432	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:28:27.254733+03	مسؤول كلية	تكافل	\N
433	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:28:27.866933+03	مسؤول كلية	تكافل	\N
434	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:29:58.448295+03	مسؤول كلية	تكافل	\N
435	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:29:58.520727+03	مسؤول كلية	تكافل	\N
436	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:30:22.0038+03	مسؤول كلية	تكافل	\N
437	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 01:30:22.174734+03	مسؤول كلية	تكافل	\N
438	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 02:07:05.225066+03	مسؤول كلية	تكافل	\N
439	17	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 02:07:05.371244+03	مسؤول كلية	تكافل	\N
440	8	إنشاء نشاط جديد "معرض" للخطة "خطة ا"	74	\N	\N	\N	2026-05-08 02:19:01.42532+03	مسؤول كلية	نشاط	\N
441	24	إنشاء نشاط جديد "المرعض" للخطة "خطة قسم ثقافي"	75	\N	\N	\N	2026-05-08 02:22:05.810888+03	مدير ادارة	نشاط	\N
442	17	الموافقة المبدئية على طلب التكافل	\N	17	\N	127.0.0.1	2026-05-08 15:19:55.905753+03	مسؤول كلية	تكافل	\N
443	17	الموافقة على طلب التكافل	\N	17	\N	127.0.0.1	2026-05-08 15:20:21.113927+03	مسؤول كلية	تكافل	\N
444	17	رفض طلب التكافل	\N	17	\N	127.0.0.1	2026-05-08 15:21:05.89424+03	مسؤول كلية	تكافل	\N
445	17	رفض طلب التكافل	\N	17	\N	127.0.0.1	2026-05-08 15:40:24.673492+03	مسؤول كلية	تكافل	\N
446	10	رفض مشرف النظام لطلب تكافل	\N	17	\N	127.0.0.1	2026-05-08 15:54:52.330583+03	مشرف النظام	تكافل	\N
447	10	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 15:55:46.937263+03	مشرف النظام	تكافل	\N
448	10	عرض مستندات الطلب	\N	17	\N	127.0.0.1	2026-05-08 15:56:09.501536+03	مشرف النظام	تكافل	\N
449	10	موافقة مشرف النظام على طلب تكافل	\N	17	\N	127.0.0.1	2026-05-08 16:29:50.756049+03	مشرف النظام	تكافل	\N
450	20	رفض نشاط: المرعض	75	\N	\N	127.0.0.1	2026-05-09 01:40:49.335078+03	مدير كلية	نشاط	\N
\.


--
-- Data for Name: plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plans (plan_id, name, term, created_at, updated_at, faculty_id, dept_id, created_by) FROM stdin;
4	plan2026	1	2026-02-15 16:10:54.641662+02	2026-02-15 16:10:54.641672+02	1	\N	\N
2	plan2026	1	2026-02-15 16:08:27.490535+02	2026-02-15 16:08:27.490544+02	\N	\N	\N
9	pp	1	2026-03-07 00:19:43.209025+02	2026-03-07 00:19:43.209032+02	1	\N	8
13	خطةأ  ا	2	2026-03-07 08:09:28.304535+02	2026-03-07 08:09:28.304547+02	\N	\N	16
10	خطة 5	2	2026-03-07 07:53:29.417557+02	2026-03-07 08:18:40.035077+02	1	\N	8
7	test3	2	2026-03-06 02:59:01.863291+02	2026-03-06 02:59:01.863301+02	1	\N	\N
15	خطة للأنشطة الثقافية	2	2026-03-13 00:29:23.14286+02	2026-03-13 00:30:59.237743+02	3	\N	22
16	خطة قسم ثقافي	2	2026-03-13 03:36:08.544512+02	2026-03-13 03:36:08.544524+02	\N	\N	24
6	test3	2	2026-03-06 02:58:38.741921+02	2026-03-06 02:58:38.741933+02	1	\N	\N
12	خطةأ  ا	2	2026-03-07 07:58:16.958054+02	2026-03-07 07:58:16.958063+02	\N	\N	16
14	خطةأ  ا	2	2026-03-07 08:09:43.86666+02	2026-03-07 08:09:43.866671+02	\N	\N	16
1	العام الدراسي 2025-2026	2	2026-02-15 16:07:55.641683+02	2026-02-15 16:23:03.518843+02	1	\N	8
5	string505050	1	2026-02-15 16:36:57.167863+02	2026-03-06 05:18:28.715085+02	\N	\N	16
8	string5005050r	1	2026-03-06 04:41:50.468994+02	2026-03-07 00:31:20.296824+02	1	\N	8
11	خطة ا	2	2026-03-07 07:54:32.912134+02	2026-05-08 02:20:20.122404+03	1	1	8
\.


--
-- Data for Name: posts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.posts (post_id, title, description, family_id, faculty_id, created_at, updated_at) FROM stdin;
1	test	first test for posts at family 1	1	1	2025-12-06 23:37:53.830965	2025-12-06 23:37:53.830977
2	hellooo	this is a hello	20	1	2025-12-12 00:09:07.412746	2025-12-12 00:09:07.412758
3	hello	test post	6	1	2026-01-19 00:32:56.010437	2026-01-19 00:32:56.010449
\.


--
-- Data for Name: prtcps; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.prtcps (event_id, student_id, rank, reward, status, id) FROM stdin;
3	13	\N	\N	منتظر	3
6	2	\N	\N	مقبول	2
6	13	\N	\N	مقبول	4
6	11	\N	\N	مرفوض	1
55	13	\N	\N	منتظر	5
62	13	\N	\N	منتظر	11
65	37	\N	\N	منتظر	16
\.


--
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.refresh_tokens (id, user_id, user_type, token_hash, created_at, expires_at, is_revoked, ip_address, device_info) FROM stdin;
7	13	student	86c7e016f7fef2f35585e25d1d86d068fa0fba39613814a7b4e235c17a411b74	2026-04-27 23:43:48.692744+03	2026-05-04 23:43:48.692559+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
8	13	student	7364048ea1cc68e3bf7fc3b165d379d481b6417fb6c9050b8852650dd0e86b8c	2026-04-27 23:46:48.883115+03	2026-05-04 23:46:48.882996+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
9	13	student	d5008f337fc06dd7bb576149921622590fde3e759c50b0f8aa0a759ba163bae3	2026-04-27 23:46:59.242186+03	2026-05-04 23:46:59.242063+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
10	13	student	77839b6d0b01ca252e5e972e0b56e272ab3283ce2f05870f73dd8ea9243de063	2026-04-27 23:47:00.366232+03	2026-05-04 23:47:00.366127+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
1	13	student	4315e6166c9031bfe9ec40e691fcc9bf09856d715ee2dd96e6d094dd98429042	2026-04-27 23:23:23.313656+03	2026-05-04 23:23:23.313458+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
2	13	student	38da8fadb9de81fd67193eebc7f911e95325327896aa9a929af8d298e2c7d0c4	2026-04-27 23:25:11.767218+03	2026-05-04 23:25:11.767092+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
3	13	student	b91f09be847361747b85cefbec86155385888f2439c10bbafef349a85d91c84a	2026-04-27 23:28:32.404612+03	2026-05-04 23:28:32.404499+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
4	13	student	a27a67ea32983f951cc28b3179015254c7118172cd460bf6094c070275cfacec	2026-04-27 23:30:20.647322+03	2026-05-04 23:30:20.647208+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
5	13	student	7dd8cf4d71e15207b4a7a54ff61e03a3d0581414969f4fa2c3d05b2d13288db7	2026-04-27 23:33:18.558034+03	2026-05-04 23:33:18.557921+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
6	13	student	d1b77da9a7bb46fecd987ea3c1d7bd00ba2d673c8e3e8b99481500c2289740ce	2026-04-27 23:38:14.374244+03	2026-05-04 23:38:14.374112+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
11	13	student	a08abcb8d8b0ba0f12e20ec7f4e1ce9596c384575f2ac17b3fabfaadc72225b4	2026-04-27 23:57:30.1332+03	2026-05-04 23:57:30.133053+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
12	13	student	d1b6733bd04be718c58b39eaba1bae279ed7c7fee438981412eb0e4bee663ae6	2026-04-28 00:03:56.648846+03	2026-05-05 00:03:56.648723+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
13	10	admin	6c3cf3f496395a3ec468ce5fb5dde012f0781e543fd8c8eabfbde8d9bfe8b84c	2026-04-28 00:05:14.72382+03	2026-05-05 00:05:14.723686+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
14	10	admin	464a84d6b6c2175b7d36a48596e42b37af9cb31bed6a15de1614fe983b5aee84	2026-04-28 00:06:20.04433+03	2026-05-05 00:06:20.044196+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
15	8	admin	91a3771e012a1838f7c1cadc28145c1e91bceec286eb86f629ca217dd8756e58	2026-04-28 01:38:54.506105+03	2026-05-05 01:38:54.505926+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
16	8	admin	821f31f932101c5c8ce38b0ebda4cf65928d133f973166d5e6f3cd87796b3e81	2026-04-28 01:42:54.471737+03	2026-05-05 01:42:54.471613+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
17	8	admin	52c4a442ac1abb4571da2fb5a244ebe4090b29b6921a2f9ccd77051c40b07007	2026-04-28 01:43:12.641381+03	2026-05-05 01:43:12.641286+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
18	8	admin	de8f2b1756b8e078e85b1826ef5ac0bb8c66872615736490ff179a5fc5a694b7	2026-04-28 01:53:13.646982+03	2026-05-05 01:53:13.646734+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
19	13	student	98cc442c4e6f07e3762fba741cbd03ca83c21c0445a3c56727944dff63d4f823	2026-04-28 02:03:21.676271+03	2026-05-05 02:03:21.676073+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
20	24	admin	93a57cac017892e3359f699b7acff088363c5e252ba131f0b60cab5f22951aa2	2026-04-28 17:29:45.969788+03	2026-05-05 17:29:45.969471+03	f	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
21	8	admin	41bd34a9598b3cffa63defef0fefa81c60d4811649b3efd66c724e490beed0e5	2026-04-28 17:31:24.754091+03	2026-05-05 17:31:24.753971+03	f	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
22	8	admin	b9ac1cc7b4b76e0a1ee0b5019bf481339ebbd3e73304e9b60d2ec63514c8194a	2026-04-28 17:33:42.010544+03	2026-05-05 17:33:42.010366+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
23	8	admin	edc1d4fb63d8f1a032bf5128c603da3679fba49f4abc456bdf14f591c85f2fe4	2026-04-28 22:55:18.170323+03	2026-05-05 22:55:18.170039+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
24	8	admin	1c537805a0fff3d0fe3d919c49442f2516a3b012702b37bfa35b53ce7a5bbda1	2026-04-28 22:55:56.785157+03	2026-05-05 22:55:56.784979+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
25	8	admin	87bdb5bf46eb1a7552af0ba01b88ad7801155b690f3f0e92513e42898417da84	2026-04-28 22:56:55.745136+03	2026-05-05 22:56:55.744985+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
26	8	admin	1a3d845467f50251e971228e710fce09bc839a80a941eae64d3ba0acc5a1deab	2026-04-28 22:57:31.048904+03	2026-05-05 22:57:31.048647+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
27	8	admin	8fa878461d1aa9a8b11ae46f68af52774d23678ee85b9f03cacf7395f083d2a8	2026-04-28 22:58:35.328314+03	2026-05-05 22:58:35.328139+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
28	8	admin	82828bcb79a4d25523f26fd4240ff98bc8598ef956cea24f67a09327d4645187	2026-04-28 22:59:11.42393+03	2026-05-05 22:59:11.423738+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
29	8	admin	8c8668fc7350b2fb800829cfa3f63cecd6b1a211c237e9e92415ac63e718c63b	2026-04-28 22:59:28.680335+03	2026-05-05 22:59:28.680013+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
30	8	admin	580b55c143df0314574e37c7c549d38c0aaa4580c5a6cb65d7f3fc88d06d35fc	2026-04-28 22:59:46.443874+03	2026-05-05 22:59:46.443674+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
31	8	admin	2551e58f4db292ec64daac1f000de83e1447a420965e6edc85072a043043aa34	2026-04-28 22:59:52.566287+03	2026-05-05 22:59:52.566057+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
32	8	admin	17fd47e085d5f5f20b07e85f925a51fbdfc4445cdeda146f98a5b96c080b5973	2026-04-28 22:59:59.33743+03	2026-05-05 22:59:59.33722+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
33	8	admin	0cd8c5755896690e14f4e504695534b81796888d95cbbe4a2d678df1e5326e25	2026-04-28 23:00:26.835394+03	2026-05-05 23:00:26.83521+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
34	8	admin	e2e31cb4ee820ae2af93134758c8896cef907cc4077a1e4bd4716bca4a05fbbd	2026-04-28 23:00:32.927314+03	2026-05-05 23:00:32.927146+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
35	8	admin	9f130f9290a592c36667fe4d4c224fceea362791d6352fefa722ddffbdaabd9a	2026-04-28 23:00:38.099056+03	2026-05-05 23:00:38.098888+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
36	8	admin	e83ea744dbf994a218ce0ccd991d517c3aa9ffb44c0e9fd4abb5cbb53ecb54d9	2026-04-28 23:00:59.842138+03	2026-05-05 23:00:59.841911+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
37	8	admin	c3f7d00da7f7baaac3e0dfb3fae26d3e5b828e2541940b870a07c37d953e9cbb	2026-04-28 23:02:30.129828+03	2026-05-05 23:02:30.129666+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
38	8	admin	d01fcb1b78b9fd35a0f12de4fe3518fdae37526d204c50ddffaad2c3ff3fa5dc	2026-04-28 23:03:01.502826+03	2026-05-05 23:03:01.502498+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
39	8	admin	d39b2172407369214393f457a004b8b2ce506f6d717dd281fa6cf541a3e581b4	2026-04-28 23:28:39.222871+03	2026-05-05 23:28:39.222676+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
40	8	admin	4cd52dc2529732fcafc1198c98738f7fdeb3ded0c904b923b8af6a3e0ba7b909	2026-04-28 23:28:47.063385+03	2026-05-05 23:28:47.063265+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
41	8	admin	d9775c5314b38c5add8c0e1664343a0c8b222ceac33cb3d189342a8241733a80	2026-04-28 23:28:55.137793+03	2026-05-05 23:28:55.137685+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
42	8	admin	7ab08132ab9292abcc19bd7227c2b77dc858f3a80554c7bc5d56f07df6f96a02	2026-04-28 23:29:21.387587+03	2026-05-05 23:29:21.387445+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
43	8	admin	819df4dfe18ec63cd648f455bce606ce37d8007c8ec28fc54b793168b31c7d88	2026-04-28 23:29:33.520057+03	2026-05-05 23:29:33.519931+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
44	8	admin	b2a597f3c7042dfaead5621fd93136aa959b3e6ec2bacf728164258380583996	2026-04-28 23:29:41.447968+03	2026-05-05 23:29:41.447841+03	f	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
45	8	admin	28d01fd590dcdc7aaa822f98e77b344aa43a21f9eb23efb3ca5cd86b3d798205	2026-04-28 23:29:56.212296+03	2026-05-05 23:29:56.212191+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
46	8	admin	d3c26c8e865c8520f46bad75538ce495dbcd93fbeafd769d24654fae914afef4	2026-04-28 23:30:19.231154+03	2026-05-05 23:30:19.231029+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
47	8	admin	3b22d594ba208739b2f406f479ede7f0ef14adaa087d7e2d61df0447d708c189	2026-04-28 23:31:10.808265+03	2026-05-05 23:31:10.808139+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
48	8	admin	169587531793c9e13e806b620911be75dc3263c5caa07de4652da1607dddfc3a	2026-04-28 23:31:18.531717+03	2026-05-05 23:31:18.531584+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
50	5	admin	0991ce7b4accd3e998f0252deb509fdf8ab9d03636b5b6c148e8785e328c65e7	2026-04-29 00:15:53.012905+03	2026-05-06 00:15:53.012695+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
51	5	admin	64c928afb95b34e4ebcec8cd93ceba4f08dfb6db63fc07321199c74a634ef21e	2026-04-29 00:17:00.144223+03	2026-05-06 00:17:00.144069+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
49	8	admin	ff2a1aa936f6c60d3f298af18fe365b342b29bd57767b2ba47cbd57a1b11b972	2026-04-28 23:31:25.968688+03	2026-05-05 23:31:25.968555+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
52	8	admin	0158bad02dfb5a1f40232b86df5d05f64a35b57123051c843daf37ba919ea8b6	2026-04-29 00:17:38.090181+03	2026-05-06 00:17:38.090076+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
53	5	admin	f085d111c047f9bb156fd6c04ea1f987685e81015d303d4659c71a2e722f8761	2026-04-29 00:21:03.115402+03	2026-05-06 00:21:03.115269+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
54	5	admin	e6ad302b75ede5bf3c2a21ad0dd925048b5eadc1cb7be4cfb6587e4d3582101b	2026-04-29 00:21:09.846762+03	2026-05-06 00:21:09.846672+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
55	6	admin	f25378316fe8b43a7730c14fe7d86fd5692263ff8900f6c3db5f3af0c8e88d23	2026-04-29 00:26:11.259971+03	2026-05-06 00:26:11.259828+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
56	10	admin	e8a0fba2eac5882b11a08b8613f19782cbe21818f70a47e244a66de212ef28c0	2026-04-29 00:47:15.626118+03	2026-05-06 00:47:15.625906+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
57	10	admin	9cc4060a60f2d267c2581f13cef40dfef257f60f4e38a8e22d69dd7daa5424ad	2026-04-29 00:58:23.715003+03	2026-05-06 00:58:23.714762+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
58	10	admin	e605c06648e672a9eb2f71cfb39ab84ab1f8fe33a2b0a4c0928fb08add133211	2026-04-29 00:58:37.240166+03	2026-05-06 00:58:37.240016+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
59	10	admin	4ee9d79548901a221837834fa2eb52777f26a92f8014a665aaa8dc3b4c37667a	2026-04-29 00:58:40.320292+03	2026-05-06 00:58:40.320195+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
60	10	admin	801fea79aae8447c77fd0536316d0cdbe94189b62faa8a16d8f3879b05669079	2026-05-07 22:36:15.240183+03	2026-05-14 22:36:15.239531+03	t	127.0.0.1	Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36
61	10	admin	fd603c15e823b61ffc0dc2dbca9e13cbe739d5b669e92eb00d19251b4568b604	2026-05-07 22:49:11.69908+03	2026-05-14 22:49:11.698947+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
62	10	admin	5cbb5851931a1a2630ad8fbbb04400f9b5d35b1618f51e2385f80009dd292ace	2026-05-07 22:49:12.328809+03	2026-05-14 22:49:12.328679+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
63	17	admin	9d6d5cd00fc79ed4982de6d7dc1f6e75d227ca8ffb7139e97d003b635ee742cb	2026-05-07 22:50:19.237313+03	2026-05-14 22:50:19.237181+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
64	10	admin	a98aeeb7d9417a47ff48d9d2b8a22f212538cf0c552427ca75b6b62d3da62a33	2026-05-07 22:50:49.236265+03	2026-05-14 22:50:49.236046+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
65	17	admin	4f00316ab61fcf9cc5e5f1b2c74f943f9fd3c0e0e827e537882e48227405a631	2026-05-07 22:55:43.15225+03	2026-05-14 22:55:43.152135+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
66	17	admin	61c76d10b020a4c9a9308d66235d28e73fc86e998febf549bdf8870b7a7ea4fa	2026-05-07 22:55:59.424788+03	2026-05-14 22:55:59.424684+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
67	17	admin	7d19f9685115fbea25ca4bb70a3cb677d749877ca89695f79f0eb15cdf2c6cc8	2026-05-07 22:56:00.211785+03	2026-05-14 22:56:00.211671+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
68	10	admin	8554c40132d3af2914a8c39396ba68747bf4a6925ef1b2452574edea73cf0f19	2026-05-07 23:00:07.301229+03	2026-05-14 23:00:07.301021+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
69	10	admin	1d90e34302b8ed09c23fee0e99f0d4dfc58c72c1225981b063ba87b0598e1a07	2026-05-07 23:49:05.550324+03	2026-05-14 23:49:05.550173+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
70	10	admin	75f04be5093636b5867cb33d08a3bde0ee760d5eee076bc81112d496775b7995	2026-05-07 23:50:31.578572+03	2026-05-14 23:50:31.578365+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
71	10	admin	415eb622ed371aad6a5af7c1c67f31c86b2397ad22aec82122c5f8b8b0c695ed	2026-05-07 23:53:42.772976+03	2026-05-14 23:53:42.772853+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
72	10	admin	e6f61d10860069cd7aebd1d3d473ea23468fd81520c0b297616cfea125f39e2b	2026-05-07 23:58:58.683826+03	2026-05-14 23:58:58.683711+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
73	10	admin	e73cee06983680e6953b7a888ab14d3c492bfbaba5d3c13085c74754f3646717	2026-05-07 23:59:00.032808+03	2026-05-14 23:59:00.032709+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
74	10	admin	e2beef59dca426ebe2ef34640d057dd35c1a92b2b459cb70eb7225f4c326cd27	2026-05-08 00:40:44.444837+03	2026-05-15 00:40:44.44473+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
75	10	admin	78650a40561fe772c531ef66b2bbb1585ee96effa70a82a3d654088dab972587	2026-05-08 00:49:34.011449+03	2026-05-15 00:49:34.011303+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
77	17	admin	600d0dabaa15df41f223f758c288d5eaaaa6645192229510a7c12597da47cc18	2026-05-08 00:55:50.605909+03	2026-05-15 00:55:50.605747+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
76	17	admin	a04ce2ac639fc5d3eae9df5ad5cd76ff65693151f7418a165ebaeeee524102d8	2026-05-08 00:51:13.275234+03	2026-05-15 00:51:13.275097+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
78	17	admin	7e3b81a68f5b816660b5ad1fad70bb619c8bd3ed72ff14bc1ede222ee3afff83	2026-05-08 00:55:59.245415+03	2026-05-15 00:55:59.245306+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
79	17	admin	7943f286394babd8d4ef49d88533b340bf19ea9ca512280c1961db4ea77d1d49	2026-05-08 00:58:46.364663+03	2026-05-15 00:58:46.364536+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
80	10	admin	f869a49a90c89bed874ee40cf8d1dfe40876f01a57010c944b4f6ffb7699763e	2026-05-08 01:18:48.750583+03	2026-05-15 01:18:48.750295+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
81	17	admin	006ab762098f737c6133838d3ab48b8e5cc46a4ddc4d53b1e63507c3106d0aa4	2026-05-08 01:24:50.863046+03	2026-05-15 01:24:50.862736+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
82	17	admin	e5cb0dc4333618f9be4e53dbe16441765c0d7f3a95650a7e8a6ef63f680f8024	2026-05-08 01:25:15.664263+03	2026-05-15 01:25:15.664116+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
83	17	admin	97e7e2c4449a6167fbed97347e1a566099ff48a266a539b03c3021bae7820a11	2026-05-08 01:25:44.350189+03	2026-05-15 01:25:44.34989+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
84	17	admin	33f9fc1851f46fcf95ae2ce8a1c0f932e2dd25a9cd9d6ba18d38195af4184ead	2026-05-08 01:26:53.185028+03	2026-05-15 01:26:53.184856+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
85	17	admin	92592f3da8b50d03b6658913eca1a59b66967a77da2eda56bbb4d67091ea1c1d	2026-05-08 01:27:14.33414+03	2026-05-15 01:27:14.334019+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
86	17	admin	8bd4fdaeedaf4957ab6605a7a5c43dbc6ae15da79857225a9aefc26809b433b6	2026-05-08 01:28:05.441418+03	2026-05-15 01:28:05.441309+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
87	17	admin	c5f13fd0018be7e8af02ac18bc5b559ff324e5edcfb7e561f771f76b1d239942	2026-05-08 02:06:29.480438+03	2026-05-15 02:06:29.479872+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
88	13	student	f1abed089c79c9c0fc8288a8457210e6460639afaf1ba46ef181f4bd16fcee98	2026-05-08 02:10:11.602064+03	2026-05-15 02:10:11.601917+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
89	13	student	f54a393368a3e1af1718937602d9f36da6716678e479ff4171c408312304e5c5	2026-05-08 02:10:14.009309+03	2026-05-15 02:10:14.009169+03	t	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
90	13	student	d7bd813812c624cdd60bc72e26694bc0cb3934ee2a1d74436bb7dcda163cfb19	2026-05-08 02:10:14.243517+03	2026-05-15 02:10:14.243405+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
91	17	admin	1f21ab8cc1505ae1905a4dcaf9f4576485a147e02b3eee1a75130c59fa724cd6	2026-05-08 02:17:18.535783+03	2026-05-15 02:17:18.535636+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
92	8	admin	8a4b3f18a4f0d8d69cb9b711c8a8a6de6580d39ca3d827fe6e59ac9463467941	2026-05-08 02:17:42.349148+03	2026-05-15 02:17:42.349037+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
93	24	admin	de1b44f17abd7bfdbcc1d1bd9d6d1cc568a7770c3e61a70559e959a6598476c2	2026-05-08 02:21:19.401664+03	2026-05-15 02:21:19.401538+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
94	17	admin	270f071f055abf45375fbbe0cca8a65389737d8ca0cc732944bda32742f10711	2026-05-08 15:17:59.547934+03	2026-05-15 15:17:59.547684+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
95	17	admin	d7e0f23524e50c90176db82bda848446cb6fb88d77bcec8c0dbec99a6e1b6b2d	2026-05-08 15:18:06.845183+03	2026-05-15 15:18:06.845055+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
96	17	admin	7590765dfc2193d92a81f2fe834d81cd335bbed621040786a69974bd3cc46724	2026-05-08 15:39:40.117499+03	2026-05-15 15:39:40.117236+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
97	17	admin	c130d8e54e5d084706cde4c21d3636a95479ce143f954c5ff8adbb2d921e0a89	2026-05-08 15:39:46.222265+03	2026-05-15 15:39:46.22212+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
98	17	admin	b15c442cdf7b0f1d06909ffd05f633e2c5a3555f51ae0c88d7bcbeb3f271882e	2026-05-08 15:48:02.346732+03	2026-05-15 15:48:02.346532+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
99	17	admin	2a91422d9e7ddc66bdd67bfde7d7cf622106ba30a4067b2db3b020e0ebbc0680	2026-05-08 15:48:11.808005+03	2026-05-15 15:48:11.807884+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
100	13	student	faec1134f7755190d75bf38dc72803912f38334681337b75ab58efc687d09702	2026-05-08 15:52:09.719831+03	2026-05-15 15:52:09.719478+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
101	10	admin	beb648e08eca10846cd8df5379448fc3ff8eb7776445dc170e548968619a6570	2026-05-08 15:53:53.362865+03	2026-05-15 15:53:53.362302+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
102	10	admin	61c7f7d72bd839a1f8ad03977945d76ad399875d42b0cc490bf7f6f5a17be210	2026-05-08 15:54:35.714841+03	2026-05-15 15:54:35.714687+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
103	10	admin	e306de51fae4fce33a1ef034bcb08c1e665c72342d7189ff20b5b247b44ecdb0	2026-05-08 15:54:44.617943+03	2026-05-15 15:54:44.617805+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
104	10	admin	65ffa5b118038160ce2bffa59a74176194ad48f8ada9635f580e45db4486529c	2026-05-08 16:20:47.319353+03	2026-05-15 16:20:47.319141+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
105	10	admin	b113f32c93a582110b35b989e164dfbbc32be065e37a23bf0ab524a70b1b1f84	2026-05-08 16:20:54.022495+03	2026-05-15 16:20:54.022346+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
106	10	admin	892adc494baadf11df30641a0a729b526f20a17466df5c3ad9fb137826a3a189	2026-05-08 16:49:28.101421+03	2026-05-15 16:49:28.101198+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
107	17	admin	a115825ac8280e43c1138da870472941adfb62077aa8ac2e70d33b3531901cfa	2026-05-08 16:49:50.493415+03	2026-05-15 16:49:50.493291+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0
108	17	admin	c4cc0aa310014095b7e34cc9a96f6b6992805ca5ac02ceafe4376f550d7007c4	2026-05-09 01:34:46.906209+03	2026-05-16 01:34:46.906007+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0
109	20	admin	aa56422e74b1758e0a552b59c6e31e4136d89f4c0454f40e9d0ecd08f59a7da7	2026-05-09 01:39:27.013968+03	2026-05-16 01:39:27.013832+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0
110	10	admin	6b814ca5eb730443278ef668a6dd7c66abd03a1d9c70842516ea8c3a85c5c31d	2026-05-09 02:29:33.074673+03	2026-05-16 02:29:33.07446+03	f	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0
\.


--
-- Data for Name: scout_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scout_members (scout_member_id, student_id, clan_id, group_id, role, status, reviewed_by, rejection_reason, reviewed_at, joined_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: solidarities; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solidarities (solidarity_id, student_id, faculty_id, req_status, created_at, family_numbers, father_status, mother_status, father_income, mother_income, total_income, arrange_of_brothers, m_phone_num, f_phone_num, reason, disabilities, grade, acd_status, address, approved_by, updated_at, req_type, housing_status, total_discount, sd, discount_type, rejection_reason) FROM stdin;
26	22	1	مرفوض	2025-11-22 16:53:59.746127+02	1	string	string	400.00	200.00	600.00	1	201222222	2012366666	string	t	جيد	full	eg	12	2025-11-22 18:12:01.346154+02	\N	ملك	\N	f	{}	\N
7	2	2	مرفوض	2025-10-28 01:24:54.463617+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	11	2025-11-09 23:32:48.53273+02	\N	ملك	\N	f	{}	\N
2	2	2	مرفوض	2025-10-28 00:56:10.499315+03	9	حي	حية	50000.00	1000.00	51000.00	2	+201578963214	+201578963214	دعم خصم	no	ممتاز	انتساب	ايجبت	7	2025-10-28 01:02:03.629864+03	\N	ايجار	\N	f	{}	\N
3	2	2	مرفوض	2025-10-28 01:13:32.31247+03	10	حلو	حلوة	100000.00	500000.00	600000.00	7	+201578963214	+201578963214	صاشف	f	جيد جدا	انتظام	ايجيبت	7	2025-10-28 01:14:47.758265+03	\N	ملك	\N	f	{}	\N
4	2	2	مرفوض	2025-10-28 01:17:55.946147+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	7	2025-10-28 01:19:53.839019+03	\N	ملك	\N	f	{}	\N
5	2	2	مرفوض	2025-10-28 01:20:02.365943+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	7	2025-10-28 01:21:07.755414+03	\N	ملك	\N	f	{}	\N
6	2	2	مرفوض	2025-10-28 01:21:12.208124+03	1	string	string	10.00	1.00	11.00	1	+201578963214	+201578963214	string	t	string	string	string	7	2025-10-28 01:24:50.378357+03	\N	ملك	\N	f	{}	\N
27	22	1	مقبول	2025-11-22 20:38:22.990429+02	5	working	working	200.00	200.00	400.00	2	+201215458777	+201225887745	uit98t7	نعم	امتياز	انتظام	eg	8	2025-11-22 21:11:35.528508+02	\N	ملك	600	f	{"خصم كتاب","خصم انتساب"}	\N
28	22	1	مقبول	2025-11-22 21:25:05.521407+02	5	working	working	200.00	200.00	400.00	2	+201254578545	+201254578555	rture	نعم	امتياز	انتظام	eg	8	2025-11-22 21:26:29.8242+02	\N	ملك	1700	f	{"خصم كتاب","خصم انتظام"}	\N
1	2	2	مرفوض	2025-10-27 18:03:25.391324+03	7	بالمعاش	ربة منزل	700.00	0.00	700.00	2	+201587489632	+201578963214	احتياج الدعم	لا	جيد	ناجح	مصر	11	2026-04-18 01:50:30.343107+02	\N	ملك	400	f	{}	\N
45	13	1	مرفوض	2026-03-15 04:18:39.175729+02	50	string	string	800.00	800.00	1600.00	20	+14606246837	+168043865	string	لا	string	string	string	11	2026-04-18 03:38:47.802861+02	\N	ملك	\N	f	{}	\N
46	13	1	مقبول	2026-03-15 04:30:12.187209+02	50	string	string	800.00	800.00	1600.00	20	+14606246837	+168043865	string	لا	string	string	string	11	2026-04-19 13:29:38.22503+02	\N	ملك	\N	f	{}	\N
18	14	2	مرفوض	2025-11-14 16:37:31.209661+02	1	string	string	7054.00	9.00	7063.00	1	+202222222	+20122222	string	f	جيد	ناجح	eg	10	2026-04-29 00:58:48.828742+03	\N	ملك	\N	f	{}	2
47	37	3	مرفوض	2026-04-24 15:29:34.266776+03	5	مريض	متوفاة	500.00	0.00	500.00	5	01212125545	01221212121	dfdsfgd	نعم	امتياز	انتساب	fdيباسايس	10	2026-04-29 00:59:12.512028+03	\N	ملك	\N	f	{}	2
17	2	2	مقبول	2025-11-10 03:36:29.746581+02	1	string	string	200.00	200.00	400.00	1	+202558789	+2056797987	string	t	string	string	ed	10	2026-05-08 16:29:50.756049+03	\N	ملك	1000	f	{"خصم كامل"}	\N
\.


--
-- Data for Name: solidarity_docs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solidarity_docs (doc_id, solidarity_id, doc_type, mime_type, file_size, uploaded_at, file) FROM stdin;
58	17	بحث احتماعي	image/jpeg	23818	2025-11-10 03:36:29.752539+02	uploads/solidarity/17/1.jpg
59	17	اثبات دخل	image/jpeg	14318	2025-11-10 03:36:29.755902+02	uploads/solidarity/17/2.jpg
60	17	ص.ب ولي امر	image/jpeg	23818	2025-11-10 03:36:29.75754+02	uploads/solidarity/17/1_ziCDGz3.jpg
61	17	ص.ب شخصية	image/png	10998	2025-11-10 03:36:29.759617+02	uploads/solidarity/17/3.png
62	17	حبازة زراعية	image/png	145558	2025-11-10 03:36:29.761375+02	uploads/solidarity/17/postgres_-_public.png
63	17	تكافل و كرامة	image/jpeg	7046	2025-11-10 03:36:29.763004+02	uploads/solidarity/17/4.jpg
64	18	بحث احتماعي	image/jpeg	23818	2025-11-14 16:37:31.225708+02	uploads/solidarity/18/1.jpg
65	18	اثبات دخل	image/jpeg	14318	2025-11-14 16:37:31.230888+02	uploads/solidarity/18/2.jpg
151	45	بحث احتماعي	image/jpeg	23818	2026-03-15 04:18:39.176953+02	private/solidarity/45/50239d7e5cb946e2b92c92eacc9172ba.jpg
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
152	45	اثبات دخل	image/jpeg	14318	2026-03-15 04:18:39.179679+02	private/solidarity/45/22fb0a62bbd0444dbed04a84157204d9.jpg
153	45	ص.ب ولي امر	image/png	10998	2026-03-15 04:18:39.186604+02	private/solidarity/45/15cfe6191d8d405881b183208f39860c.png
154	45	ص.ب شخصية	image/jpeg	7046	2026-03-15 04:18:39.188491+02	private/solidarity/45/da0bfece0da04b7c8a87f8f0565a4490.jpg
155	46	بحث احتماعي	image/jpeg	23818	2026-03-15 04:30:12.188425+02	private/solidarity/46/b86205c59d2d42aab76d620b49a0fe88.jpg
156	46	اثبات دخل	image/jpeg	14318	2026-03-15 04:30:12.195837+02	private/solidarity/46/b07bedb982a545beb0aa6aa60983fe75.jpg
157	46	ص.ب ولي امر	image/png	10998	2026-03-15 04:30:12.197406+02	private/solidarity/46/9bfbaf8fc59445029864920c48fd980a.png
158	46	ص.ب شخصية	image/jpeg	7046	2026-03-15 04:30:12.198884+02	private/solidarity/46/94de9cdd705f44a58842f88f19648ccd.jpg
159	47	بحث احتماعي	image/jpeg	83040	2026-04-24 15:29:34.270195+03	private/solidarity/47/532d5b704b594a308e28b2184e0fb8e3.jpeg
160	47	اثبات دخل	image/png	804	2026-04-24 15:29:34.275668+03	private/solidarity/47/4a4c2d38c89640ebab3b6799c9768941.png
161	47	ص.ب ولي امر	image/jpeg	141430	2026-04-24 15:29:34.277143+03	private/solidarity/47/8d3f40276198479bb9d88e2008537d9a.jpg
162	47	ص.ب شخصية	application/pdf	941521	2026-04-24 15:29:34.283318+03	private/solidarity/47/94d51aca887e4bc9a536f1ee56749e02.pdf
\.


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.students (student_id, name, email, password, faculty_id, profile_photo, gender, nid, uid, phone_number, address, acd_year, join_date, gpa, grade, major, google_id, google_picture, is_google_auth, auth_method, last_login_method, last_google_login, can_create_fam) FROM stdin;
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
28	aloalo	alolo@gmail.com	$2b$12$MMVtnfjNS8aWKC4V.plX1ObsIyAtsphd1tKE7pramj5ZoHE7e.sUy	1	\N	m	20121545478454	252525	+20121221212	egypt	1	2025-12-02	\N	\N	sw	\N	\N	f	email	\N	\N	t
15	std2	std2@gmail.com	$2b$12$SngL6dkYpJ4WEPMQ2URgqOS4i4yBR1QGgHgWzJzqsmX9NawEBZhru	1	uploads/students/15/image.jpg	M	2021254587	2021245	+201254578	eg	4	2025-11-14	\N	ممتاز	sw	\N	\N	f	email	\N	\N	t
36	علي	ali5@gmail.com	$2b$12$lVLBcoy0XpkOnR2BEHF.hOZ2i69cCOXas.dtibIA5ed30n1kZgLf6	3	\N	M	201212548789666	20121210	20124545255	egypt	1	2025-12-04	\N	\N	sw	\N	\N	f	email	\N	\N	f
39	test2	omarsomaa1na@gmail.com	$2b$12$ZHnIEwjU0DPI.RItAqdxwuqpuNwsK/vLEBut6i9Xpdu5RXBG4jXmO	1	\N	m	20255555555557	34235	2012222277	string	string	2026-01-17	\N	string	string	\N	\N	f	email	\N	\N	f
38	test	test@gmail.com	$2b$12$BmXBa75oYnvp938Ak2mTwe//1uqRabCui3RNL7mz7af75f70Qdioe	1	\N	m	gAAAAABpa46bTpr2_6EudLrpOGB-3l0EHSPsC7k5_M9i2tPDnMqTfwYhyhQpz4bpLEoGaTXTGu68Vui9sQX5Ivgfb9ILtN40Sg==	gAAAAABpa46bKy9cA6u63ZCKnzWim5dwcbAjeWFltHGqW6P2xnvX0cN2qknajz3QY72DHaAt-6Wqlut6zK6I3LMWb7CngZOecA==	gAAAAABpa46bHBXFLnrKkRsAfB3rtoFXD_9RwT1hqdu1PH5Oblo9JCpB-lU0m9SB9Awi-AmD-5yil78W85gTP5Tn0cpWXwdAjg==	gAAAAABpa46b4ShYUDqT9bO914NaCmsQ7LevnDse6JGULVKiryPs-MgUAkJKi_YnN0pJZzAeo4sO8EZIBT98sq7YaFNA6uV18Q==	string	2026-01-17	\N	string	string	\N	\N	f	email	\N	\N	f
40	string2	string2@gmail.com	$2b$12$dTPIFTFZpdcNfObrttdfWeOnJMcNm9nMlyf4XvYSx8NSSHM8sOmvK	1	uploads/students/40/image.jpg	m	20222121212154	2025055	20122222555	string	string	2026-03-09	\N	string	string	\N	\N	f	email	\N	\N	f
1	محمد سعيد	m.saeed@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	uploads/students/1/image.jpg	M	123456789	987654321	555222222	string	string	2025-09-01	\N	string	string	\N	\N	f	email	\N	\N	t
2	ليلى خالد	l.khaled@example.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	uploads/students/2/image.png	F	223456789	887654321	55522220	string	string	2025-09-01	\N	string	string	\N	\N	f	email	\N	\N	f
11	A	AA@gmail.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	\N	F	50248798655487	55857	20125455485	Eg	2025	2025-09-01	\N	\N	hg	\N	\N	f	email	\N	\N	t
41	احمد محمد عبدالعليم	ahmed@gmail.com	$2b$12$YnVs0gcSte2Y819L3CC2l.7j7gzeHrwlF7RCbP/DGKCv4ZtsRTQry	3	\N	M	30306285457439	22121213	01020038432	المعادي	الفرقة الثالثة	2026-04-19	\N	جيد جدا	علاج طبيعي	\N	\N	f	email	\N	\N	t
37	ssh	ssh493147@gmail.com	$2b$12$JPbqOqj6x7c.E2WpLzYiieWdZBmv4pl5rFwKib8mT3yrlzYnPIfQy	3	\N	M	201215458747845	20121545	20124504850	egypt	one	2025-12-09	\N	\N	sdfs	108654151463126841079	https://lh3.googleusercontent.com/a/ACg8ocJOdPnMOecixsR8HSe3rh1b64btth_Gn1n3zcDYWxRxa71-BQ=s96-c	t	google	google	2026-04-24 12:24:58.346457	f
13	S	s@gmail.com	$2b$12$/yfBp5mpBNUt4EZp1IWEJu22QNUjejzEuBB/0JiUNeZ.32HPn7SOq	1	uploads/students/13/image.jpg	F	50248798445487	57857	5552222	string	الفرقة الاولى	2025-09-01	\N	string	string	\N	\N	f	email	\N	\N	f
\.


--
-- Name: admins_admin_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.admins_admin_id_seq', 26, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 108, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, false);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: clan_groups_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.clan_groups_group_id_seq', 1, false);


--
-- Name: clans_clan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.clans_clan_id_seq', 1, false);


--
-- Name: departments_dept_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.departments_dept_id_seq', 11, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 27, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 25, true);


--
-- Name: documents_doc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documents_doc_id_seq', 2, true);


--
-- Name: event_docs_doc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.event_docs_doc_id_seq', 26, true);


--
-- Name: events_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.events_event_id_seq', 75, true);


--
-- Name: faculties_faculty_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.faculties_faculty_id_seq', 3, true);


--
-- Name: families_family_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.families_family_id_seq', 21, true);


--
-- Name: family_admins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.family_admins_id_seq', 60, true);


--
-- Name: logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.logs_log_id_seq', 450, true);


--
-- Name: plans_plan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plans_plan_id_seq', 16, true);


--
-- Name: posts_post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.posts_post_id_seq', 3, true);


--
-- Name: prtcps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.prtcps_id_seq', 16, true);


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.refresh_tokens_id_seq', 110, true);


--
-- Name: scout_members_scout_member_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scout_members_scout_member_id_seq', 1, false);


--
-- Name: solidarities_solidarity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solidarities_solidarity_id_seq', 47, true);


--
-- Name: solidarity_docs_doc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solidarity_docs_doc_id_seq', 162, true);


--
-- Name: students_student_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.students_student_id_seq', 41, true);


--
-- Name: admins admins_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_email_key UNIQUE (email);


--
-- Name: admins admins_national_id_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_national_id_unique UNIQUE (nid);


--
-- Name: admins admins_phone_number_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_phone_number_unique UNIQUE (phone_number);


--
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (admin_id);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: clan_groups clan_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clan_groups
    ADD CONSTRAINT clan_groups_pkey PRIMARY KEY (group_id);


--
-- Name: clans clans_faculty_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clans
    ADD CONSTRAINT clans_faculty_id_key UNIQUE (faculty_id);


--
-- Name: clans clans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clans
    ADD CONSTRAINT clans_pkey PRIMARY KEY (clan_id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (dept_id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (doc_id);


--
-- Name: event_docs event_docs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_docs
    ADD CONSTRAINT event_docs_pkey PRIMARY KEY (doc_id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (event_id);


--
-- Name: faculties faculties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculties
    ADD CONSTRAINT faculties_pkey PRIMARY KEY (faculty_id);


--
-- Name: families families_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_pkey PRIMARY KEY (family_id);


--
-- Name: family_admins family_admins_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_admins
    ADD CONSTRAINT family_admins_pkey PRIMARY KEY (id);


--
-- Name: family_members family_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_pkey PRIMARY KEY (family_id, student_id);


--
-- Name: logs logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (log_id);


--
-- Name: plans plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_pkey PRIMARY KEY (plan_id);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (post_id);


--
-- Name: prtcps prtcps_event_student_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_event_student_unique UNIQUE (event_id, student_id);


--
-- Name: prtcps prtcps_id_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_id_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: scout_members scout_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scout_members
    ADD CONSTRAINT scout_members_pkey PRIMARY KEY (scout_member_id);


--
-- Name: solidarities solidarities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_pkey PRIMARY KEY (solidarity_id);


--
-- Name: solidarity_docs solidarity_docs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarity_docs
    ADD CONSTRAINT solidarity_docs_pkey PRIMARY KEY (doc_id);


--
-- Name: solidarity_docs solidarity_docs_solidarity_id_doc_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarity_docs
    ADD CONSTRAINT solidarity_docs_solidarity_id_doc_type_key UNIQUE (solidarity_id, doc_type);


--
-- Name: students students_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_email_key UNIQUE (email);


--
-- Name: students students_google_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_google_id_key UNIQUE (google_id);


--
-- Name: students students_nid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_nid_key UNIQUE (nid);


--
-- Name: students students_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_phone_number_key UNIQUE (phone_number);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (student_id);


--
-- Name: students students_uid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_uid_key UNIQUE (uid);


--
-- Name: scout_members unique_student_clan; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scout_members
    ADD CONSTRAINT unique_student_clan UNIQUE (student_id, clan_id);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: idx_admins_dept_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_admins_dept_id ON public.admins USING btree (dept_id);


--
-- Name: idx_admins_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_admins_faculty_id ON public.admins USING btree (faculty_id);


--
-- Name: idx_event_docs_event; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_event_docs_event ON public.event_docs USING btree (event_id);


--
-- Name: idx_event_docs_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_event_docs_event_id ON public.event_docs USING btree (event_id);


--
-- Name: idx_event_docs_uploaded_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_event_docs_uploaded_at ON public.event_docs USING btree (uploaded_at DESC);


--
-- Name: idx_event_docs_uploaded_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_event_docs_uploaded_by ON public.event_docs USING btree (uploaded_by);


--
-- Name: idx_events_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_created_by ON public.events USING btree (created_by);


--
-- Name: idx_events_dept_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_dept_id ON public.events USING btree (dept_id);


--
-- Name: idx_events_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_faculty_id ON public.events USING btree (faculty_id);


--
-- Name: idx_events_plan_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_plan_id ON public.events USING btree (plan_id) WITH (deduplicate_items='true');


--
-- Name: idx_events_selected_facs; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_selected_facs ON public.events USING gin (selected_facs);


--
-- Name: idx_families_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_families_created_by ON public.families USING btree (created_by);


--
-- Name: idx_families_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_families_faculty_id ON public.families USING btree (faculty_id);


--
-- Name: idx_family_admins_family_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_family_admins_family_id ON public.family_admins USING btree (family_id);


--
-- Name: idx_family_members_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_family_members_student ON public.family_members USING btree (student_id);


--
-- Name: idx_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_action ON public.logs USING btree (action);


--
-- Name: idx_logs_actor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_actor_id ON public.logs USING btree (actor_id);


--
-- Name: idx_logs_logged_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_logged_at ON public.logs USING btree (logged_at);


--
-- Name: idx_logs_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_student_id ON public.logs USING btree (student_id) WITH (fillfactor='100', deduplicate_items='true');


--
-- Name: idx_logs_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logs_target ON public.logs USING btree (target_type, event_id, solidarity_id, family_id);


--
-- Name: idx_plans_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plans_created_by ON public.plans USING btree (created_by);


--
-- Name: idx_plans_dept_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plans_dept_id ON public.plans USING btree (dept_id);


--
-- Name: idx_plans_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plans_faculty_id ON public.plans USING btree (faculty_id);


--
-- Name: idx_plans_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plans_name ON public.plans USING btree (name) WITH (fillfactor='100', deduplicate_items='true');


--
-- Name: idx_posts_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_posts_created_at ON public.posts USING btree (created_at DESC);


--
-- Name: idx_posts_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_posts_faculty_id ON public.posts USING btree (faculty_id);


--
-- Name: idx_posts_family_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_posts_family_id ON public.posts USING btree (family_id);


--
-- Name: idx_prtcps_event; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prtcps_event ON public.prtcps USING btree (event_id);


--
-- Name: idx_prtcps_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prtcps_student ON public.prtcps USING btree (student_id);


--
-- Name: idx_refresh_tokens_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_tokens_expires ON public.refresh_tokens USING btree (expires_at) WHERE (is_revoked = false);


--
-- Name: idx_refresh_tokens_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_tokens_hash ON public.refresh_tokens USING btree (token_hash) WHERE (is_revoked = false);


--
-- Name: idx_refresh_tokens_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_tokens_user ON public.refresh_tokens USING btree (user_type, user_id);


--
-- Name: idx_solidarities_faculty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_solidarities_faculty ON public.solidarities USING btree (faculty_id);


--
-- Name: idx_solidarities_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_solidarities_student ON public.solidarities USING btree (student_id);


--
-- Name: idx_students_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_students_faculty_id ON public.students USING btree (faculty_id);


--
-- Name: events trg_events_touch; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_events_touch BEFORE UPDATE ON public.events FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: families trg_families_touch; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_families_touch BEFORE UPDATE ON public.families FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: solidarities trg_solidarities_touch; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_solidarities_touch BEFORE UPDATE ON public.solidarities FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: admins admins_dept_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_dept_fk FOREIGN KEY (dept_id) REFERENCES public.departments(dept_id) ON DELETE SET NULL;


--
-- Name: admins admins_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: event_docs event_docs_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_docs
    ADD CONSTRAINT event_docs_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(event_id) ON DELETE CASCADE;


--
-- Name: event_docs event_docs_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_docs
    ADD CONSTRAINT event_docs_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: events events_created_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_created_by_fk FOREIGN KEY (created_by) REFERENCES public.admins(admin_id) ON DELETE RESTRICT;


--
-- Name: events events_dept_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_dept_fk FOREIGN KEY (dept_id) REFERENCES public.departments(dept_id) ON DELETE SET NULL;


--
-- Name: events events_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: events events_plan_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_plan_fk FOREIGN KEY (plan_id) REFERENCES public.plans(plan_id) ON DELETE SET NULL;


--
-- Name: families families_approved_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_approved_by_fk FOREIGN KEY (approved_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: families families_created_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_created_by_fk FOREIGN KEY (created_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: families families_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: family_members family_members_family_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_family_fk FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE CASCADE;


--
-- Name: family_members family_members_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE CASCADE;


--
-- Name: family_admins fk_admin_family; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_admins
    ADD CONSTRAINT fk_admin_family FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE CASCADE;


--
-- Name: clans fk_clan_admin; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clans
    ADD CONSTRAINT fk_clan_admin FOREIGN KEY (created_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: clans fk_clan_faculty; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clans
    ADD CONSTRAINT fk_clan_faculty FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE CASCADE;


--
-- Name: events fk_events_family; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_events_family FOREIGN KEY (family_id) REFERENCES public.families(family_id);


--
-- Name: family_members fk_family_members_dept; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT fk_family_members_dept FOREIGN KEY (dept_id) REFERENCES public.departments(dept_id);


--
-- Name: clan_groups fk_group_clan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clan_groups
    ADD CONSTRAINT fk_group_clan FOREIGN KEY (clan_id) REFERENCES public.clans(clan_id) ON DELETE CASCADE;


--
-- Name: scout_members fk_member_admin; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scout_members
    ADD CONSTRAINT fk_member_admin FOREIGN KEY (reviewed_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: scout_members fk_member_clan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scout_members
    ADD CONSTRAINT fk_member_clan FOREIGN KEY (clan_id) REFERENCES public.clans(clan_id) ON DELETE CASCADE;


--
-- Name: scout_members fk_member_group; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scout_members
    ADD CONSTRAINT fk_member_group FOREIGN KEY (group_id) REFERENCES public.clan_groups(group_id) ON DELETE SET NULL;


--
-- Name: scout_members fk_member_student; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scout_members
    ADD CONSTRAINT fk_member_student FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE CASCADE;


--
-- Name: posts fk_posts_faculty; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_posts_faculty FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE CASCADE;


--
-- Name: posts fk_posts_family; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_posts_family FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE CASCADE;


--
-- Name: logs logs_actor_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_actor_fk FOREIGN KEY (actor_id) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: logs logs_event_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_event_fk FOREIGN KEY (event_id) REFERENCES public.events(event_id) ON DELETE SET NULL;


--
-- Name: logs logs_family_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_family_fk FOREIGN KEY (family_id) REFERENCES public.families(family_id) ON DELETE SET NULL;


--
-- Name: logs logs_solidarity_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_solidarity_fk FOREIGN KEY (solidarity_id) REFERENCES public.solidarities(solidarity_id) ON DELETE SET NULL;


--
-- Name: logs logs_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE SET NULL;


--
-- Name: plans plans_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: plans plans_dept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_dept_id_fkey FOREIGN KEY (dept_id) REFERENCES public.departments(dept_id) ON DELETE SET NULL;


--
-- Name: plans plans_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: prtcps prtcps_event_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_event_fk FOREIGN KEY (event_id) REFERENCES public.events(event_id) ON DELETE CASCADE;


--
-- Name: prtcps prtcps_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prtcps
    ADD CONSTRAINT prtcps_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE CASCADE;


--
-- Name: solidarities solidarities_approved_by_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_approved_by_fk FOREIGN KEY (approved_by) REFERENCES public.admins(admin_id) ON DELETE SET NULL;


--
-- Name: solidarities solidarities_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE SET NULL;


--
-- Name: solidarities solidarities_student_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarities
    ADD CONSTRAINT solidarities_student_fk FOREIGN KEY (student_id) REFERENCES public.students(student_id) ON DELETE SET NULL;


--
-- Name: solidarity_docs solidarity_docs_solidarity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solidarity_docs
    ADD CONSTRAINT solidarity_docs_solidarity_id_fkey FOREIGN KEY (solidarity_id) REFERENCES public.solidarities(solidarity_id) ON DELETE CASCADE;


--
-- Name: students students_faculty_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_faculty_fk FOREIGN KEY (faculty_id) REFERENCES public.faculties(faculty_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict FgEvPnb4vKUwFhebrlXhcLLcPEu5bhbQ9n1fkcbffSU0NIiS54C4DuqyRWdLH24

