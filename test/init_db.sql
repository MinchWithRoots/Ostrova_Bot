-- Очистка таблиц (если нужно)
DELETE FROM Users;
DELETE FROM Clubs;
DELETE FROM Club_Schedule;
DELETE FROM Events;
DELETE FROM FAQ;

-- Заполнение таблицы Users
INSERT INTO Users (first_name, last_name, birthdate, phone) VALUES
('Иван', 'Иванов', '2000.05.10', '89111234567'),
('Мария', 'Смирнова', '2001.06.12', '89222345678');

-- Заполнение таблицы Clubs
INSERT INTO Clubs (name, active) VALUES
('Программирование', 1),
('Дизайн', 1);

-- Заполнение Club_Schedule
INSERT INTO Club_Schedule (club_id, date, day_of_week, start_time, end_time, max_participants, current_participants) VALUES
(1, '2025-04-05', 'Saturday', '15:00', '17:00', 10, 0),
(2, '2025-04-06', 'Sunday', '10:00', '12:00', 8, 0);

-- Заполнение Events
INSERT INTO Events (name, description, date, time, location, max_participants, current_participants, active) VALUES
('Концерт', 'Открытый микрофон', '2025-04-10', '18:00', 'Зал "Охта"', 30, 0, 1);

-- Заполнение FAQ
INSERT INTO FAQ (question, answer) VALUES
('Как записаться?', 'Через бота в разделе "Кружки и Мероприятия"'),
('Где проходят занятия?', 'Адрес: Санкт-Петербург, Корнея Чуковского, д.3');
