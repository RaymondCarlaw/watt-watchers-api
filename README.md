# Watt Watchers V3 API
This is a python framework for working with Watt Watchers V3 REST API
This requires Python 3.6+

This is not a pip library, but you are welcome to clone this repository and include in your own project.

## How to use
Create a client using the watt watchers api key you copied from their portal. Remember to include the *key_* component at the front.
> client = Client('<api_key>')
> devices = client.devices()
> for d in devices:
>     model = d.Model
>     shortEnergy = client.shortEnergy(d.Id)
>     longEnergy = client.longEnergy(d.Id)
>     modbusData = client.modbus(d.Id)

## Dependencies
* Marshmallow
* Marshmallow_dataclass