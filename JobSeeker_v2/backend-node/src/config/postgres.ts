import { Sequelize } from 'sequelize';
import dotenv from 'dotenv';

dotenv.config();

export const sequelize = new Sequelize(
  process.env.DB_NAME || 'jobseeker',
  process.env.DB_USER || 'postgres',
  process.env.DB_PASS || 'postgres',
  {
    host: process.env.DB_HOST || 'localhost',
    dialect: 'postgres',
    logging: false,
  }
);

export const connectPostgres = async () => {
  try {
    await sequelize.authenticate();
    console.log('PostgreSQL connected.');
    await sequelize.sync(); // Auto-create tables (dev only)
  } catch (error) {
    console.error('Unable to connect to PostgreSQL:', error);
  }
};
