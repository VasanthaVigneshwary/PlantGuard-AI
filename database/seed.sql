--
-- PostgreSQL database dump
--

\restrict 5j0SlSHH7PK0ApZTYwqAckIhunvVr7y31quMoK5ZrP6Zncqts3zfwExc0E30EBM

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

--
-- Data for Name: crops; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.crops (id, name, scientific_name, description, created_at) VALUES (1, 'Tomato', 'Solanum lycopersicum', 'A widely cultivated vegetable crop commonly affected by fungal, bacterial, and viral diseases.', '2026-09-14 18:32:18.436146');
INSERT INTO public.crops (id, name, scientific_name, description, created_at) VALUES (2, 'Potato', 'Solanum tuberosum', 'A major food crop that can be affected by fungal and bacterial diseases.', '2026-09-14 18:32:18.436146');
INSERT INTO public.crops (id, name, scientific_name, description, created_at) VALUES (3, 'Rice', 'Oryza sativa', 'A major cereal crop commonly affected by fungal, bacterial, and viral diseases.', '2026-09-14 18:32:18.436146');
INSERT INTO public.crops (id, name, scientific_name, description, created_at) VALUES (4, 'Cotton', 'Gossypium', 'An important fiber crop affected by various fungal, bacterial, viral, and pest-related problems.', '2026-09-14 18:32:18.436146');
INSERT INTO public.crops (id, name, scientific_name, description, created_at) VALUES (5, 'Chilli', 'Capsicum annuum', 'A spice and vegetable crop commonly affected by fungal, bacterial, and viral diseases.', '2026-09-14 18:32:18.436146');


--
-- Data for Name: diseases; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (1, 1, 'Tomato Late Blight', 'A destructive fungal-like disease that causes dark lesions on leaves, stems, and fruits.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (2, 1, 'Tomato Early Blight', 'A fungal disease that commonly causes dark concentric spots on tomato leaves.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (3, 1, 'Tomato Leaf Mold', 'A fungal disease that produces yellow patches on the upper leaf surface and mold growth underneath.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (4, 2, 'Potato Late Blight', 'A serious disease that causes dark lesions on potato leaves and can affect tubers.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (5, 2, 'Potato Early Blight', 'A fungal disease characterized by dark concentric lesions on potato leaves.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (6, 3, 'Rice Blast', 'A fungal disease that can affect rice leaves, nodes, and panicles.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (7, 3, 'Rice Brown Spot', 'A fungal disease that produces brown lesions on rice leaves and grains.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (8, 4, 'Cotton Leaf Curl Disease', 'A viral disease that causes leaf curling, vein thickening, and abnormal plant growth.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (9, 4, 'Cotton Bacterial Blight', 'A bacterial disease that can cause angular leaf spots, blighting, and boll symptoms.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (10, 5, 'Chilli Anthracnose', 'A fungal disease that causes dark sunken lesions on chilli fruits.', '2026-09-14 18:34:27.130043');
INSERT INTO public.diseases (id, crop_id, name, description, created_at) VALUES (11, 5, 'Chilli Leaf Curl Disease', 'A viral disease that causes leaf curling, distortion, and reduced plant growth.', '2026-09-14 18:34:27.130043');


--
-- Data for Name: treatments; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (1, 1, 'Late Blight Management', 'Disease management', 'Integrated management of tomato late blight using sanitation, environmental management, resistant varieties, and approved plant protection measures.', 'Remove severely infected plant material where appropriate, improve airflow, avoid prolonged leaf wetness, monitor the crop regularly, and follow locally approved disease-management recommendations.', 'Use only products approved for the crop and disease in the relevant region. Follow the product label and required safety precautions.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (2, 2, 'Early Blight Management', 'Disease management', 'Integrated management of tomato early blight using sanitation, crop monitoring, healthy planting material, and appropriate plant protection practices.', 'Remove infected plant debris where appropriate, maintain field sanitation, monitor symptoms regularly, and follow locally approved management recommendations.', 'Follow the product label and local agricultural recommendations. Use appropriate protective equipment when required.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (3, 3, 'Leaf Mold Management', 'Disease management', 'Management of tomato leaf mold through humidity and moisture management, sanitation, and crop monitoring.', 'Improve air circulation, reduce prolonged leaf wetness, remove affected material where appropriate, and monitor the crop regularly.', 'Avoid unnecessary chemical applications and follow locally approved recommendations.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (4, 4, 'Potato Late Blight Management', 'Disease management', 'Integrated management of potato late blight using healthy planting material, sanitation, environmental management, and approved plant protection measures.', 'Use healthy planting material, monitor the crop, improve field conditions, and follow locally approved late-blight management recommendations.', 'Follow product labels and regional recommendations for any plant protection product used.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (5, 5, 'Potato Early Blight Management', 'Disease management', 'Management of potato early blight through sanitation, healthy planting material, crop monitoring, and suitable plant protection practices.', 'Maintain field sanitation, use healthy planting material, monitor crops regularly, and follow locally approved recommendations.', 'Use only approved products and follow label directions and safety requirements.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (6, 6, 'Rice Blast Management', 'Disease management', 'Integrated management of rice blast using resistant varieties, crop monitoring, balanced crop nutrition, and locally recommended disease-management practices.', 'Monitor plants regularly, maintain balanced nutrition, and use suitable resistant varieties where available.', 'Avoid excessive or unbalanced fertilizer application. Follow local agricultural recommendations.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (7, 7, 'Rice Brown Spot Management', 'Disease management', 'Management of rice brown spot through balanced nutrition, suitable irrigation, crop monitoring, and appropriate crop management.', 'Maintain suitable irrigation, support balanced crop nutrition, and monitor plants regularly.', 'Management should be adapted to local soil, climate, and crop conditions.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (8, 8, 'Cotton Leaf Curl Disease Management', 'Disease management', 'Management of cotton leaf curl disease focuses on reducing virus-vector pressure, crop monitoring, healthy planting material, and resistant varieties where available.', 'Monitor plants and vector populations, use healthy planting material, and select suitable resistant varieties where available.', 'Vector management should follow locally approved integrated pest management recommendations.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (9, 9, 'Cotton Bacterial Blight Management', 'Disease management', 'Management of cotton bacterial blight through sanitation, healthy planting material, moisture management, and crop monitoring.', 'Use healthy planting material, maintain field sanitation, reduce unnecessary leaf wetness, and monitor the crop regularly.', 'Follow locally approved recommendations for any plant protection product.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (10, 10, 'Chilli Anthracnose Management', 'Disease management', 'Integrated management of chilli anthracnose through sanitation, moisture management, healthy planting material, and crop monitoring.', 'Remove infected plant material where appropriate, improve airflow, avoid prolonged leaf wetness, and monitor fruits regularly.', 'Use only approved plant protection products and follow label instructions.', '2026-09-14 18:43:18.75476');
INSERT INTO public.treatments (id, disease_id, name, type, description, instructions, precautions, created_at) VALUES (11, 11, 'Chilli Leaf Curl Disease Management', 'Disease management', 'Management of chilli leaf curl disease focuses on vector management, healthy planting material, crop monitoring, and resistant varieties where available.', 'Monitor crops and insect vectors, use healthy planting material, and select suitable resistant varieties where available.', 'Follow locally approved integrated pest management recommendations.', '2026-09-14 18:43:18.75476');


--
-- Data for Name: application_rates; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (1, 1, 'Foliar spray', 'ml/acre', 80.0000, 'per acre', 'Cyazofamid 34.5% SC. Source: TNAU Agritech Portal, Tomato Late Blight. Verify current product label and local approval before use.');
INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (2, 1, 'Foliar spray', 'ml/acre', 200.0000, 'per acre', 'Azoxystrobin 23% SC. Source: TNAU Agritech Portal, Tomato Late Blight. Verify current product label and local approval before use.');
INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (3, 1, 'Foliar spray', 'g/acre', 1000.0000, 'per acre', 'Mancozeb 35% SC. Source: TNAU Agritech Portal, Tomato Late Blight. Verify current product label and local approval before use.');
INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (4, 1, 'Foliar spray', 'g/acre', 800.0000, 'per acre', 'Zineb 75% WP. Source: TNAU Agritech Portal, Tomato Late Blight. Verify current product label and local approval before use.');
INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (5, 2, 'Foliar spray', 'ml/acre', 200.0000, 'per acre', 'Azoxystrobin 23% SC. Source: TNAU Agritech Portal, Tomato Early Blight. Verify current product label and local approval before use.');
INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (6, 2, 'Foliar spray', 'g/acre', 1000.0000, 'per acre', 'Mancozeb 35% SC. Source: TNAU Agritech Portal, Tomato Early Blight. Verify current product label and local approval before use.');
INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (7, 2, 'Foliar spray', 'kg/acre', 1.0000, 'per acre', 'Metiram 70% WG. Source: TNAU Agritech Portal, Tomato Early Blight. Verify current product label and local approval before use.');
INSERT INTO public.application_rates (id, treatment_id, application_method, measurement_unit, rate, basis, notes) VALUES (8, 2, 'Foliar spray', 'g/acre', 200.0000, 'per acre', 'Pyraclostrobin 20% WG. Source: TNAU Agritech Portal, Tomato Early Blight. Verify current product label and local approval before use.');


--
-- Data for Name: causes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.causes (id, name, description) VALUES (1, 'High humidity', 'High relative humidity can favor development and spread of several plant diseases.');
INSERT INTO public.causes (id, name, description) VALUES (2, 'Excess leaf wetness', 'Prolonged moisture on leaves can create favorable conditions for some fungal and bacterial diseases.');
INSERT INTO public.causes (id, name, description) VALUES (3, 'Poor air circulation', 'Dense plant growth and limited airflow can increase humidity around leaves and encourage disease development.');
INSERT INTO public.causes (id, name, description) VALUES (4, 'Infected plant material', 'Diseased seeds, seedlings, plant debris, or infected tissues can introduce or spread pathogens.');
INSERT INTO public.causes (id, name, description) VALUES (5, 'Poor field sanitation', 'Unremoved infected plant debris can allow disease-causing organisms to persist and spread.');
INSERT INTO public.causes (id, name, description) VALUES (6, 'Infected planting material', 'Using infected seed, tubers, cuttings, or seedlings can introduce disease into a crop.');
INSERT INTO public.causes (id, name, description) VALUES (7, 'Water stress', 'Insufficient or irregular water availability can weaken plants and increase susceptibility to some diseases.');
INSERT INTO public.causes (id, name, description) VALUES (8, 'Nutrient imbalance', 'Improper nutrient availability can weaken plant growth and increase susceptibility to disease.');
INSERT INTO public.causes (id, name, description) VALUES (9, 'Vector transmission', 'Certain plant viruses can be transmitted by insect vectors such as whiteflies or aphids.');
INSERT INTO public.causes (id, name, description) VALUES (10, 'Favorable temperature', 'Temperature conditions suitable for a pathogen can increase disease development and spread.');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.users (id, name, email, phone, preferred_language, created_at, updated_at) VALUES (1, 'Plant Guard User', 'plantguard@local.test', NULL, 'en', '2026-09-26 09:54:25.675036', '2026-09-26 09:54:25.675036');


--
-- Data for Name: predictions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: disease_causes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (1, 1);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (1, 2);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (1, 3);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (1, 10);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (2, 4);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (2, 5);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (2, 10);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (3, 1);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (3, 2);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (3, 3);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (4, 1);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (4, 2);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (4, 10);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (5, 4);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (5, 5);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (5, 10);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (6, 1);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (6, 10);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (6, 8);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (7, 7);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (7, 8);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (7, 10);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (8, 9);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (9, 2);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (9, 4);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (9, 5);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (10, 1);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (10, 2);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (10, 3);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (10, 10);
INSERT INTO public.disease_causes (disease_id, cause_id) VALUES (11, 9);


--
-- Data for Name: prevention; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.prevention (id, title, description) VALUES (1, 'Improve air circulation', 'Maintain suitable plant spacing and airflow to reduce prolonged humidity around foliage.');
INSERT INTO public.prevention (id, title, description) VALUES (2, 'Avoid prolonged leaf wetness', 'Use irrigation practices that minimize unnecessary moisture remaining on leaves.');
INSERT INTO public.prevention (id, title, description) VALUES (3, 'Remove infected plant material', 'Remove and properly dispose of severely infected leaves, fruits, or plant debris where appropriate.');
INSERT INTO public.prevention (id, title, description) VALUES (4, 'Maintain field sanitation', 'Keep fields and growing areas clean and remove disease-carrying plant residues.');
INSERT INTO public.prevention (id, title, description) VALUES (5, 'Use healthy planting material', 'Use healthy, disease-free seeds, seedlings, tubers, or other planting material.');
INSERT INTO public.prevention (id, title, description) VALUES (6, 'Monitor crops regularly', 'Inspect plants regularly so disease symptoms can be identified and managed early.');
INSERT INTO public.prevention (id, title, description) VALUES (7, 'Manage insect vectors', 'Monitor and manage insect vectors that can transmit plant viruses.');
INSERT INTO public.prevention (id, title, description) VALUES (8, 'Maintain balanced nutrition', 'Provide appropriate and balanced nutrients according to crop requirements and soil conditions.');
INSERT INTO public.prevention (id, title, description) VALUES (9, 'Manage irrigation', 'Provide appropriate irrigation and avoid conditions that cause excessive moisture or prolonged water stress.');
INSERT INTO public.prevention (id, title, description) VALUES (10, 'Use suitable resistant varieties', 'Where available, select crop varieties with resistance or tolerance to important diseases.');


--
-- Data for Name: disease_prevention; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (1, 1);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (1, 2);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (1, 3);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (1, 5);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (1, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (2, 3);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (2, 4);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (2, 5);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (2, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (2, 10);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (3, 1);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (3, 2);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (3, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (4, 1);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (4, 2);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (4, 3);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (4, 5);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (4, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (5, 3);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (5, 4);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (5, 5);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (5, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (5, 10);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (6, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (6, 8);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (6, 10);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (7, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (7, 8);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (7, 9);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (8, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (8, 7);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (8, 10);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (9, 2);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (9, 3);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (9, 4);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (9, 5);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (9, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (10, 1);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (10, 2);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (10, 3);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (10, 5);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (10, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (11, 6);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (11, 7);
INSERT INTO public.disease_prevention (disease_id, prevention_id) VALUES (11, 10);


--
-- Data for Name: symptoms; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.symptoms (id, name, description) VALUES (1, 'Dark leaf lesions', 'Dark or brown lesions appearing on affected leaves.');
INSERT INTO public.symptoms (id, name, description) VALUES (2, 'Concentric leaf spots', 'Circular spots with visible concentric rings on leaves.');
INSERT INTO public.symptoms (id, name, description) VALUES (3, 'Yellow leaf patches', 'Yellow discoloration or patches appearing on leaf surfaces.');
INSERT INTO public.symptoms (id, name, description) VALUES (4, 'White or gray mold growth', 'Visible mold-like growth developing on affected plant tissue.');
INSERT INTO public.symptoms (id, name, description) VALUES (5, 'Leaf curling', 'Leaves curl or roll abnormally as the disease progresses.');
INSERT INTO public.symptoms (id, name, description) VALUES (6, 'Brown leaf spots', 'Brown spots or lesions developing on leaves.');
INSERT INTO public.symptoms (id, name, description) VALUES (7, 'Diamond-shaped lesions', 'Distinctive diamond-shaped lesions appearing on rice leaves or stems.');
INSERT INTO public.symptoms (id, name, description) VALUES (8, 'Vein thickening', 'Leaf veins become thicker and more prominent than normal.');
INSERT INTO public.symptoms (id, name, description) VALUES (9, 'Fruit lesions', 'Dark or sunken lesions appearing on fruits.');
INSERT INTO public.symptoms (id, name, description) VALUES (10, 'Fruit rot', 'Affected fruits develop rotting or decaying tissue.');
INSERT INTO public.symptoms (id, name, description) VALUES (11, 'Plant stunting', 'Overall plant growth becomes slower or smaller than healthy plants.');
INSERT INTO public.symptoms (id, name, description) VALUES (12, 'Boll lesions', 'Lesions or abnormal symptoms appearing on cotton bolls.');


--
-- Data for Name: disease_symptoms; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (1, 1);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (1, 9);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (1, 10);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (2, 2);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (2, 6);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (2, 11);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (3, 3);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (3, 4);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (4, 1);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (4, 9);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (4, 10);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (5, 2);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (5, 6);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (6, 7);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (6, 11);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (7, 6);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (7, 11);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (8, 5);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (8, 8);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (8, 11);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (9, 1);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (9, 12);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (10, 9);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (10, 10);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (11, 5);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (11, 8);
INSERT INTO public.disease_symptoms (disease_id, symptom_id) VALUES (11, 11);


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.notifications (id, user_id, prediction_id, title, message, notification_type, scheduled_at, is_read, created_at) VALUES (1, 1, NULL, 'Plant health monitoring reminder', 'Review the current crop health and upload a fresh leaf image if symptoms have changed.', 'monitoring', NULL, false, '2026-09-26 04:24:25.706232');
INSERT INTO public.notifications (id, user_id, prediction_id, title, message, notification_type, scheduled_at, is_read, created_at) VALUES (2, 1, NULL, 'Regular crop inspection reminder', 'Inspect leaves, stems, and soil routinely to catch early signs of stress or disease.', 'inspection', NULL, false, '2026-09-26 04:24:25.706232');
INSERT INTO public.notifications (id, user_id, prediction_id, title, message, notification_type, scheduled_at, is_read, created_at) VALUES (3, 1, NULL, 'Disease prevention reminder', 'Keep growing areas clean, improve airflow, and remove infected plant material promptly.', 'prevention', NULL, false, '2026-09-26 04:24:25.706232');
INSERT INTO public.notifications (id, user_id, prediction_id, title, message, notification_type, scheduled_at, is_read, created_at) VALUES (4, 1, NULL, 'Treatment and application reminder', 'Follow the recommended treatment instructions and product label before applying any control measures.', 'treatment', NULL, false, '2026-09-26 04:24:25.706232');
INSERT INTO public.notifications (id, user_id, prediction_id, title, message, notification_type, scheduled_at, is_read, created_at) VALUES (5, 1, NULL, 'General plant-care reminder', 'Maintain balanced watering, soil health, and crop spacing to support strong plant growth.', 'care', NULL, false, '2026-09-26 04:24:25.706232');


--
-- Name: application_rates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.application_rates_id_seq', 8, true);


--
-- Name: causes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.causes_id_seq', 10, true);


--
-- Name: chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chat_messages_id_seq', 1, false);


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chat_sessions_id_seq', 1, false);


--
-- Name: crops_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.crops_id_seq', 5, true);


--
-- Name: diseases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.diseases_id_seq', 11, true);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notifications_id_seq', 5, true);


--
-- Name: predictions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.predictions_id_seq', 1, false);


--
-- Name: prevention_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.prevention_id_seq', 10, true);


--
-- Name: symptoms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.symptoms_id_seq', 12, true);


--
-- Name: treatments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.treatments_id_seq', 11, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 5j0SlSHH7PK0ApZTYwqAckIhunvVr7y31quMoK5ZrP6Zncqts3zfwExc0E30EBM

