package main

import (
	"context"
	"fmt"
	"log"

	"io/ioutil"

	"gopkg.in/yaml.v3"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"gopkg.in/mgo.v2/bson"
)

// This is a user defined method to close resources.
// This method closes mongoDB connection and cancel context.
func close(client *mongo.Client, ctx context.Context,
	cancel context.CancelFunc) {

	// CancelFunc to cancel to context
	defer cancel()

	// client provides a method to close
	// a mongoDB connection.
	defer func() {

		// client.Disconnect method also has deadline.
		// returns error if any,
		if err := client.Disconnect(ctx); err != nil {
			panic(err)
		}
	}()
}

func CloseClientDB(client *mongo.Client) {
	if client == nil {
		return
	}

	err := client.Disconnect(context.TODO())
	if err != nil {
		log.Fatal(err)
	}

	// TODO optional you can log your closed MongoDB client
	fmt.Println("Connection to MongoDB closed.")
}

func get_rec(user_id int, collection *mongo.Collection) (results []bson.M) {
	cursor, err := collection.Find(context.TODO(), bson.M{"USER_ID": user_id})

	if err = cursor.All(context.TODO(), &results); err != nil {
		panic(err)
	}
	return results
}

func show_results(results []bson.M) {
	for _, result := range results {
		user_id := result["USER_ID"]
		rec := result["ITEM_ID_RANK"]
		fmt.Printf("We recommend user %d to watch thess:\n", user_id)
		fmt.Println(rec)
	}
}

func main() {

	// Get Client, Context, CancelFunc and
	// err from connect method.
	yfile, err := ioutil.ReadFile("connect.yaml")
	if err != nil {

		log.Fatal(err)
	}

	data := make(map[interface{}]interface{})

	err2 := yaml.Unmarshal(yfile, &data)
	if err2 != nil {

		log.Fatal(err2)
	}

	credential := options.Credential{
		Username: data["Username"].(string),
		Password: data["Password"].(string),
	}

	clientOpts := options.Client().ApplyURI(data["URI"].(string)).SetAuth(credential)

	client, err := mongo.Connect(context.TODO(), clientOpts)
	if err != nil {
		log.Fatal(err)
	}
	collection := client.Database("zfl").Collection("inference")
	result := get_rec(148503, collection)
	show_results(result)
	CloseClientDB(client)
}
