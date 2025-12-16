import passport from 'passport';
import { Strategy as GoogleStrategy } from 'passport-google-oauth20';
import { Strategy as GitHubStrategy } from 'passport-github2';
import { ObjectId } from 'mongodb';
import { env } from './env.js';
import { getUsersCollection } from './database.js';
import { handleNewUserSignup } from '../services/email.service.js';
import type { User } from '../types/index.js';

export function configurePassport(): void {
  // Serialize user to session
  passport.serializeUser((user: Express.User, done) => {
    done(null, user._id.toString());
  });

  // Deserialize user from session
  passport.deserializeUser(async (id: string, done) => {
    try {
      const users = getUsersCollection();
      const user = await users.findOne({ _id: new ObjectId(id) });
      done(null, user as Express.User | null);
    } catch (error) {
      done(error);
    }
  });

  // Google OAuth Strategy
  if (env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET) {
    passport.use(
      new GoogleStrategy(
        {
          clientID: env.GOOGLE_CLIENT_ID,
          clientSecret: env.GOOGLE_CLIENT_SECRET,
          callbackURL: `${env.API_URL}/auth/google/callback`,
        },
        async (_accessToken, _refreshToken, profile, done) => {
          try {
            const user = await findOrCreateUser({
              provider: 'google',
              providerId: profile.id,
              email: profile.emails?.[0]?.value || '',
              displayName: profile.displayName,
              avatarUrl: profile.photos?.[0]?.value,
            });
            done(null, user as Express.User);
          } catch (error) {
            done(error as Error);
          }
        }
      )
    );
  }

  // GitHub OAuth Strategy
  if (env.GITHUB_CLIENT_ID && env.GITHUB_CLIENT_SECRET) {
    passport.use(
      new GitHubStrategy(
        {
          clientID: env.GITHUB_CLIENT_ID,
          clientSecret: env.GITHUB_CLIENT_SECRET,
          callbackURL: `${env.API_URL}/auth/github/callback`,
        },
        async (
          _accessToken: string,
          _refreshToken: string,
          profile: { id: string; emails?: { value: string }[]; displayName?: string; username?: string; photos?: { value: string }[] },
          done: (error: Error | null, user?: Express.User) => void
        ) => {
          try {
            const user = await findOrCreateUser({
              provider: 'github',
              providerId: profile.id,
              email: profile.emails?.[0]?.value || '',
              displayName: profile.displayName || profile.username || 'GitHub User',
              avatarUrl: profile.photos?.[0]?.value,
            });
            done(null, user as Express.User);
          } catch (error) {
            done(error as Error);
          }
        }
      )
    );
  }
}

async function findOrCreateUser(userData: Omit<User, '_id' | 'createdAt' | 'lastLoginAt'>): Promise<User> {
  const users = getUsersCollection();

  const existingUser = await users.findOne({
    provider: userData.provider,
    providerId: userData.providerId,
  });

  if (existingUser) {
    // Update last login
    await users.updateOne(
      { _id: existingUser._id },
      { $set: { lastLoginAt: new Date() } }
    );
    return { ...existingUser, lastLoginAt: new Date() };
  }

  // Create new user
  const newUser: User = {
    ...userData,
    createdAt: new Date(),
    lastLoginAt: new Date(),
  };

  const result = await users.insertOne(newUser);
  const createdUser = { ...newUser, _id: result.insertedId };

  // DISABLED: Email notifications
  // handleNewUserSignup(createdUser).catch((error) => {
  //   console.error('Failed to send signup emails:', error);
  // });

  console.log(`New user signed up: ${createdUser.email} (${createdUser.provider})`);
  return createdUser;
}
