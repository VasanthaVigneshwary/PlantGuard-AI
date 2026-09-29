--
-- PostgreSQL database dump
--

\restrict aXMfz8kSlw5yYKrwbYfo0GW80mkWmTIbJffb2mjZq1Ah7R9np1NCuUj3tdw4Zwc

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

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

ALTER TABLE IF EXISTS ONLY public.treatments DROP CONSTRAINT IF EXISTS fk_treatment_disease;
ALTER TABLE IF EXISTS ONLY public.predictions DROP CONSTRAINT IF EXISTS fk_prediction_user;
ALTER TABLE IF EXISTS ONLY public.predictions DROP CONSTRAINT IF EXISTS fk_prediction_disease;
ALTER TABLE IF EXISTS ONLY public.predictions DROP CONSTRAINT IF EXISTS fk_prediction_crop;
ALTER TABLE IF EXISTS ONLY public.notifications DROP CONSTRAINT IF EXISTS fk_notification_user;
ALTER TABLE IF EXISTS ONLY public.notifications DROP CONSTRAINT IF EXISTS fk_notification_prediction;
ALTER TABLE IF EXISTS ONLY public.disease_symptoms DROP CONSTRAINT IF EXISTS fk_disease_symptom_symptom;
ALTER TABLE IF EXISTS ONLY public.disease_symptoms DROP CONSTRAINT IF EXISTS fk_disease_symptom_disease;
ALTER TABLE IF EXISTS ONLY public.disease_prevention DROP CONSTRAINT IF EXISTS fk_disease_prevention_prevention;
ALTER TABLE IF EXISTS ONLY public.disease_prevention DROP CONSTRAINT IF EXISTS fk_disease_prevention_disease;
ALTER TABLE IF EXISTS ONLY public.diseases DROP CONSTRAINT IF EXISTS fk_disease_crop;
ALTER TABLE IF EXISTS ONLY public.disease_causes DROP CONSTRAINT IF EXISTS fk_disease_cause_disease;
ALTER TABLE IF EXISTS ONLY public.disease_causes DROP CONSTRAINT IF EXISTS fk_disease_cause_cause;
ALTER TABLE IF EXISTS ONLY public.chat_sessions DROP CONSTRAINT IF EXISTS fk_chat_session_user;
ALTER TABLE IF EXISTS ONLY public.chat_sessions DROP CONSTRAINT IF EXISTS fk_chat_session_prediction;
ALTER TABLE IF EXISTS ONLY public.chat_messages DROP CONSTRAINT IF EXISTS fk_chat_message_session;
ALTER TABLE IF EXISTS ONLY public.application_rates DROP CONSTRAINT IF EXISTS fk_application_rate_treatment;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.treatments DROP CONSTRAINT IF EXISTS treatments_pkey;
ALTER TABLE IF EXISTS ONLY public.symptoms DROP CONSTRAINT IF EXISTS symptoms_pkey;
ALTER TABLE IF EXISTS ONLY public.prevention DROP CONSTRAINT IF EXISTS prevention_pkey;
ALTER TABLE IF EXISTS ONLY public.predictions DROP CONSTRAINT IF EXISTS predictions_pkey;
ALTER TABLE IF EXISTS ONLY public.notifications DROP CONSTRAINT IF EXISTS notifications_pkey;
ALTER TABLE IF EXISTS ONLY public.diseases DROP CONSTRAINT IF EXISTS diseases_pkey;
ALTER TABLE IF EXISTS ONLY public.disease_symptoms DROP CONSTRAINT IF EXISTS disease_symptoms_pkey;
ALTER TABLE IF EXISTS ONLY public.disease_prevention DROP CONSTRAINT IF EXISTS disease_prevention_pkey;
ALTER TABLE IF EXISTS ONLY public.disease_causes DROP CONSTRAINT IF EXISTS disease_causes_pkey;
ALTER TABLE IF EXISTS ONLY public.crops DROP CONSTRAINT IF EXISTS crops_pkey;
ALTER TABLE IF EXISTS ONLY public.chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_pkey;
ALTER TABLE IF EXISTS ONLY public.chat_messages DROP CONSTRAINT IF EXISTS chat_messages_pkey;
ALTER TABLE IF EXISTS ONLY public.causes DROP CONSTRAINT IF EXISTS causes_pkey;
ALTER TABLE IF EXISTS ONLY public.application_rates DROP CONSTRAINT IF EXISTS application_rates_pkey;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.treatments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.symptoms ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.prevention ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.predictions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.notifications ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.diseases ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.crops ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.chat_sessions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.chat_messages ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.causes ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.application_rates ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.treatments_id_seq;
DROP TABLE IF EXISTS public.treatments;
DROP SEQUENCE IF EXISTS public.symptoms_id_seq;
DROP TABLE IF EXISTS public.symptoms;
DROP SEQUENCE IF EXISTS public.prevention_id_seq;
DROP TABLE IF EXISTS public.prevention;
DROP SEQUENCE IF EXISTS public.predictions_id_seq;
DROP TABLE IF EXISTS public.predictions;
DROP SEQUENCE IF EXISTS public.notifications_id_seq;
DROP TABLE IF EXISTS public.notifications;
DROP SEQUENCE IF EXISTS public.diseases_id_seq;
DROP TABLE IF EXISTS public.diseases;
DROP TABLE IF EXISTS public.disease_symptoms;
DROP TABLE IF EXISTS public.disease_prevention;
DROP TABLE IF EXISTS public.disease_causes;
DROP SEQUENCE IF EXISTS public.crops_id_seq;
DROP TABLE IF EXISTS public.crops;
DROP SEQUENCE IF EXISTS public.chat_sessions_id_seq;
DROP TABLE IF EXISTS public.chat_sessions;
DROP SEQUENCE IF EXISTS public.chat_messages_id_seq;
DROP TABLE IF EXISTS public.chat_messages;
DROP SEQUENCE IF EXISTS public.causes_id_seq;
DROP TABLE IF EXISTS public.causes;
DROP SEQUENCE IF EXISTS public.application_rates_id_seq;
DROP TABLE IF EXISTS public.application_rates;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: application_rates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_rates (
    id integer NOT NULL,
    treatment_id integer NOT NULL,
    application_method character varying(100),
    measurement_unit character varying(50),
    rate numeric(10,4),
    basis character varying(100),
    notes text
);


--
-- Name: application_rates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.application_rates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: application_rates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.application_rates_id_seq OWNED BY public.application_rates.id;


--
-- Name: causes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.causes (
    id integer NOT NULL,
    name character varying(150) NOT NULL,
    description text
);


--
-- Name: causes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.causes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: causes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.causes_id_seq OWNED BY public.causes.id;


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    session_id integer NOT NULL,
    role character varying(20) NOT NULL,
    message text NOT NULL,
    language character varying(10) DEFAULT 'en'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_chat_message_role CHECK (((role)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying])::text[])))
);


--
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_sessions (
    id integer NOT NULL,
    user_id integer,
    prediction_id integer,
    language character varying(10) DEFAULT 'en'::character varying,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_sessions_id_seq OWNED BY public.chat_sessions.id;


--
-- Name: crops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crops (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    scientific_name character varying(150),
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: crops_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.crops_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crops_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.crops_id_seq OWNED BY public.crops.id;


--
-- Name: disease_causes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_causes (
    disease_id integer NOT NULL,
    cause_id integer NOT NULL
);


--
-- Name: disease_prevention; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_prevention (
    disease_id integer NOT NULL,
    prevention_id integer NOT NULL
);


--
-- Name: disease_symptoms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_symptoms (
    disease_id integer NOT NULL,
    symptom_id integer NOT NULL
);


--
-- Name: diseases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.diseases (
    id integer NOT NULL,
    crop_id integer NOT NULL,
    name character varying(150) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: diseases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.diseases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: diseases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.diseases_id_seq OWNED BY public.diseases.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    prediction_id integer,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    notification_type character varying(50),
    scheduled_at timestamp without time zone,
    is_read boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predictions (
    id integer NOT NULL,
    user_id integer,
    crop_id integer NOT NULL,
    disease_id integer,
    image_url text,
    confidence numeric(6,5),
    model_version character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.predictions_id_seq OWNED BY public.predictions.id;


--
-- Name: prevention; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prevention (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text
);


--
-- Name: prevention_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.prevention_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: prevention_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.prevention_id_seq OWNED BY public.prevention.id;


--
-- Name: symptoms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.symptoms (
    id integer NOT NULL,
    name character varying(150) NOT NULL,
    description text
);


--
-- Name: symptoms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.symptoms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: symptoms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.symptoms_id_seq OWNED BY public.symptoms.id;


--
-- Name: treatments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.treatments (
    id integer NOT NULL,
    disease_id integer NOT NULL,
    name character varying(200) NOT NULL,
    type character varying(100),
    description text,
    instructions text,
    precautions text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: treatments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.treatments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: treatments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.treatments_id_seq OWNED BY public.treatments.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(150),
    email character varying(255),
    phone character varying(20),
    preferred_language character varying(10) DEFAULT 'en'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: application_rates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_rates ALTER COLUMN id SET DEFAULT nextval('public.application_rates_id_seq'::regclass);


--
-- Name: causes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causes ALTER COLUMN id SET DEFAULT nextval('public.causes_id_seq'::regclass);


--
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- Name: chat_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions ALTER COLUMN id SET DEFAULT nextval('public.chat_sessions_id_seq'::regclass);


--
-- Name: crops id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crops ALTER COLUMN id SET DEFAULT nextval('public.crops_id_seq'::regclass);


--
-- Name: diseases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diseases ALTER COLUMN id SET DEFAULT nextval('public.diseases_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions ALTER COLUMN id SET DEFAULT nextval('public.predictions_id_seq'::regclass);


--
-- Name: prevention id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prevention ALTER COLUMN id SET DEFAULT nextval('public.prevention_id_seq'::regclass);


--
-- Name: symptoms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.symptoms ALTER COLUMN id SET DEFAULT nextval('public.symptoms_id_seq'::regclass);


--
-- Name: treatments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.treatments ALTER COLUMN id SET DEFAULT nextval('public.treatments_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: application_rates application_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_rates
    ADD CONSTRAINT application_rates_pkey PRIMARY KEY (id);


--
-- Name: causes causes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causes
    ADD CONSTRAINT causes_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: crops crops_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crops
    ADD CONSTRAINT crops_pkey PRIMARY KEY (id);


--
-- Name: disease_causes disease_causes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_causes
    ADD CONSTRAINT disease_causes_pkey PRIMARY KEY (disease_id, cause_id);


--
-- Name: disease_prevention disease_prevention_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_prevention
    ADD CONSTRAINT disease_prevention_pkey PRIMARY KEY (disease_id, prevention_id);


--
-- Name: disease_symptoms disease_symptoms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_symptoms
    ADD CONSTRAINT disease_symptoms_pkey PRIMARY KEY (disease_id, symptom_id);


--
-- Name: diseases diseases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diseases
    ADD CONSTRAINT diseases_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id);


--
-- Name: prevention prevention_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prevention
    ADD CONSTRAINT prevention_pkey PRIMARY KEY (id);


--
-- Name: symptoms symptoms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_pkey PRIMARY KEY (id);


--
-- Name: treatments treatments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.treatments
    ADD CONSTRAINT treatments_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: application_rates fk_application_rate_treatment; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_rates
    ADD CONSTRAINT fk_application_rate_treatment FOREIGN KEY (treatment_id) REFERENCES public.treatments(id) ON DELETE CASCADE;


--
-- Name: chat_messages fk_chat_message_session; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT fk_chat_message_session FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: chat_sessions fk_chat_session_prediction; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT fk_chat_session_prediction FOREIGN KEY (prediction_id) REFERENCES public.predictions(id) ON DELETE SET NULL;


--
-- Name: chat_sessions fk_chat_session_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT fk_chat_session_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: disease_causes fk_disease_cause_cause; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_causes
    ADD CONSTRAINT fk_disease_cause_cause FOREIGN KEY (cause_id) REFERENCES public.causes(id) ON DELETE CASCADE;


--
-- Name: disease_causes fk_disease_cause_disease; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_causes
    ADD CONSTRAINT fk_disease_cause_disease FOREIGN KEY (disease_id) REFERENCES public.diseases(id) ON DELETE CASCADE;


--
-- Name: diseases fk_disease_crop; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diseases
    ADD CONSTRAINT fk_disease_crop FOREIGN KEY (crop_id) REFERENCES public.crops(id) ON DELETE CASCADE;


--
-- Name: disease_prevention fk_disease_prevention_disease; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_prevention
    ADD CONSTRAINT fk_disease_prevention_disease FOREIGN KEY (disease_id) REFERENCES public.diseases(id) ON DELETE CASCADE;


--
-- Name: disease_prevention fk_disease_prevention_prevention; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_prevention
    ADD CONSTRAINT fk_disease_prevention_prevention FOREIGN KEY (prevention_id) REFERENCES public.prevention(id) ON DELETE CASCADE;


--
-- Name: disease_symptoms fk_disease_symptom_disease; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_symptoms
    ADD CONSTRAINT fk_disease_symptom_disease FOREIGN KEY (disease_id) REFERENCES public.diseases(id) ON DELETE CASCADE;


--
-- Name: disease_symptoms fk_disease_symptom_symptom; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_symptoms
    ADD CONSTRAINT fk_disease_symptom_symptom FOREIGN KEY (symptom_id) REFERENCES public.symptoms(id) ON DELETE CASCADE;


--
-- Name: notifications fk_notification_prediction; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT fk_notification_prediction FOREIGN KEY (prediction_id) REFERENCES public.predictions(id) ON DELETE SET NULL;


--
-- Name: notifications fk_notification_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: predictions fk_prediction_crop; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT fk_prediction_crop FOREIGN KEY (crop_id) REFERENCES public.crops(id) ON DELETE CASCADE;


--
-- Name: predictions fk_prediction_disease; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT fk_prediction_disease FOREIGN KEY (disease_id) REFERENCES public.diseases(id) ON DELETE SET NULL;


--
-- Name: predictions fk_prediction_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT fk_prediction_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: treatments fk_treatment_disease; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.treatments
    ADD CONSTRAINT fk_treatment_disease FOREIGN KEY (disease_id) REFERENCES public.diseases(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict aXMfz8kSlw5yYKrwbYfo0GW80mkWmTIbJffb2mjZq1Ah7R9np1NCuUj3tdw4Zwc

