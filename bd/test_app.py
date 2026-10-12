import unittest
import database

class TestDogWalkingLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Подготовка: генерируем тестовые данные перед запуском всех тестов"""
        cls.test_email = "test_user_owner@mail.ru"
        cls.test_password = "password123"
        cls.test_phone = "+7(999)000-11-22"

    def test_1_register_user(self):
        """Тест: Регистрация нового владельца"""
        user = database.register_user("Иван Тестовый", self.test_phone, self.test_email, self.test_password, False)
        
        if user != "EMAIL_EXISTS":
            self.assertIsNotNone(user)
            self.assertEqual(user['role_name'], "владелец")
            self.assertEqual(user['email'], self.test_email)

    def test_2_authenticate_user(self):
        """Тест: Авторизация существующего пользователя"""
        user = database.authenticate_user(self.test_email, self.test_password)
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], self.test_email)
        
        bad_user = database.authenticate_user(self.test_email, "wrong_pass")
        self.assertIsNone(bad_user)

    def test_3_get_breeds(self):
        """Тест: Получение списка пород (кэш/БД)"""
        breeds = database.get_breeds()
        self.assertIsInstance(breeds, list)
        self.assertTrue(len(breeds) > 0)
        self.assertIn("name", breeds[0])

    def test_4_add_dog_and_create_order(self):
        """Тест: Добавление собаки и создание заказа"""
        user = database.authenticate_user(self.test_email, self.test_password)
        owner_id = user['id']
        
        success = database.add_dog(owner_id, "Шарик", 1, "М", "2020-01-01", "Добрый", "Нет")
        self.assertTrue(success)
        
        dogs = database.get_user_dogs(owner_id)
        self.assertTrue(len(dogs) > 0)
        dog_id = dogs[-1]['id']
        
        order_id = database.create_order(owner_id, dog_id, "2026-10-10 12:00", "2026-10-10 13:00", "ул. Тестовая, 1", "Без комментариев")
        self.assertIsNotNone(order_id)
        
        available_orders = database.get_available_orders()
        order_ids = [o['id'] for o in available_orders]
        self.assertIn(order_id, order_ids)

if __name__ == '__main__':
    unittest.main()