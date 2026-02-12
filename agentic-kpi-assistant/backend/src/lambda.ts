import serverless from "serverless-http";
import app from "./server";

// Support both API Gateway and Lambda Function URL formats
export const handler = serverless(app, {
  request: (request: any, event: any) => {
    // Handle Lambda Function URL format
    if (event.requestContext?.http) {
      request.url = event.rawPath + (event.rawQueryString ? `?${event.rawQueryString}` : '');
      request.method = event.requestContext.http.method;
    }
  }
});
