import logging

import asyncpg
import psycopg2
import psycopg2.extras
from passlib.context import CryptContext

from backend.core.config import Config

logger = logging.getLogger(__name__)

crypt_ctx = CryptContext(['pbkdf2_sha512', 'plaintext'])


def get_connection():
    return psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        connect_timeout=10,
    )


async def get_async_connection():
    return await asyncpg.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
    )


def authenticate_user(login: str, password: str):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, login, password, password_crypt, active "
            "FROM res_users WHERE login = %s AND active = true",
            (login,),
        )
        user = cur.fetchone()
        if not user:
            return None

        stored_hash = user.get('password_crypt')
        if stored_hash:
            try:
                if crypt_ctx.verify(password, stored_hash):
                    return {'id': user['id'], 'login': user['login']}
            except Exception:
                pass

        stored_plain = user.get('password')
        if stored_plain and stored_plain == password:
            return {'id': user['id'], 'login': user['login']}

        return None
    finally:
        conn.close()


def get_employee_info(user_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                e.id                        AS employee_id,
                e.name_related              AS name,
                e.emp_first_name,
                e.emp_last_name,
                e.identification_id         AS emp_code,
                e.work_email,
                e.work_phone,
                e.mobile_phone,
                e.gender,
                e.birthday,
                e.doj,
                e.lwd,
                e.marital,
                e.current_ctc,
                e.grade,
                e.emp_state,
                e.pan_number,
                e.blood_group,
                e.work_location,
                e.designation_id,
                e.department_id,
                e.parent_id,
                e.job_id,
                d.name                      AS department_name,
                des.name                    AS designation_name,
                j.name                      AS job_name,
                mgr.name_related            AS manager_name
            FROM hr_employee e
            JOIN resource_resource r ON e.resource_id = r.id
            LEFT JOIN hr_department  d   ON e.department_id  = d.id
            LEFT JOIN hr_designation des ON e.designation_id = des.id
            LEFT JOIN hr_job         j   ON e.job_id         = j.id
            LEFT JOIN hr_employee    mgr ON e.parent_id      = mgr.id
            WHERE r.user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        emp = cur.fetchone()
        return dict(emp) if emp else None
    finally:
        conn.close()


def check_is_hr(user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM res_groups_users_rel gur
                JOIN ir_model_data imd
                  ON gur.gid = imd.res_id AND imd.model = 'res.groups'
                WHERE gur.uid = %s
                  AND imd.module = 'hr'
                  AND imd.name IN ('group_hr_manager', 'group_hr_user')
            )
            """,
            (user_id,),
        )
        return bool(cur.fetchone()[0])
    finally:
        conn.close()
